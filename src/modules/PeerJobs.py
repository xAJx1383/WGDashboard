"""
Peer Jobs
"""
from .ConnectionString import ConnectionString
from .PeerJob import PeerJob
from .PeerJobLogger import PeerJobLogger
import sqlalchemy as db
from datetime import datetime
from flask import current_app

class PeerJobs:
    def __init__(self, DashboardConfig, WireguardConfigurations, AllPeerShareLinks=None):
        self.Jobs: list[PeerJob] = []
        self.engine = db.create_engine(ConnectionString('wgdashboard_job'))
        self.metadata = db.MetaData()
        self.peerJobTable = db.Table('PeerJobs', self.metadata,
                                     db.Column('JobID', db.String(255), nullable=False, primary_key=True),
                                     db.Column('Configuration', db.String(255), nullable=False),
                                     db.Column('Peer', db.String(255), nullable=False),
                                     db.Column('Field', db.String(255), nullable=False),
                                     db.Column('Operator', db.String(255), nullable=False),
                                     db.Column('Value', db.String(255), nullable=False),
                                     db.Column('CreationDate', (db.DATETIME if DashboardConfig.GetConfig("Database", "type")[1] == 'sqlite' else db.TIMESTAMP), nullable=False),
                                     db.Column('ExpireDate', (db.DATETIME if DashboardConfig.GetConfig("Database", "type")[1] == 'sqlite' else db.TIMESTAMP)),
                                     db.Column('Action', db.String(255), nullable=False),
                                     )
        self.metadata.create_all(self.engine)
        self.__getJobs()
        self.JobLogger: PeerJobLogger = PeerJobLogger(self, DashboardConfig)
        self.WireguardConfigurations = WireguardConfigurations
        self.AllPeerShareLinks = AllPeerShareLinks  # Store the reference

    def setAllPeerShareLinks(self, AllPeerShareLinks):
        """Method to set AllPeerShareLinks after initialization if needed"""
        self.AllPeerShareLinks = AllPeerShareLinks

    def __getJobs(self):
        self.Jobs.clear()
        with self.engine.connect() as conn:
            jobs = conn.execute(self.peerJobTable.select().where(
                self.peerJobTable.columns.ExpireDate.is_(None)
            )).mappings().fetchall()
            for job in jobs:
                self.Jobs.append(PeerJob(
                    job['JobID'], job['Configuration'], job['Peer'], job['Field'], job['Operator'], job['Value'],
                    job['CreationDate'], job['ExpireDate'], job['Action']))

    def getAllJobs(self, configuration: str = None):
        if configuration is not None:
            with self.engine.connect() as conn:
                jobs = conn.execute(self.peerJobTable.select().where(
                    self.peerJobTable.columns.Configuration == configuration
                )).mappings().fetchall()
                j = []
                for job in jobs:
                    j.append(PeerJob(
                        job['JobID'], job['Configuration'], job['Peer'], job['Field'], job['Operator'], job['Value'],
                        job['CreationDate'], job['ExpireDate'], job['Action']))
                return j
        return []

    def toJson(self):
        return [x.toJson() for x in self.Jobs]

    def searchJob(self, Configuration: str, Peer: str):
        return list(filter(lambda x: x.Configuration == Configuration and x.Peer == Peer, self.Jobs))

    def searchJobById(self, JobID):
        return list(filter(lambda x: x.JobID == JobID, self.Jobs))

    def saveJob(self, Job: PeerJob) -> tuple[bool, list] | tuple[bool, str]:
        import traceback
        try:
            with self.engine.begin() as conn:
                currentJob = self.searchJobById(Job.JobID)
                if len(currentJob) == 0:
                    conn.execute(
                        self.peerJobTable.insert().values(
                            {
                                "JobID": Job.JobID,
                                "Configuration": Job.Configuration,
                                "Peer": Job.Peer,
                                "Field": Job.Field,
                                "Operator": Job.Operator,
                                "Value": Job.Value,
                                "CreationDate": datetime.now(),
                                "ExpireDate": None,
                                "Action": Job.Action
                            }
                        )
                    )
                    self.JobLogger.log(Job.JobID, Message=f"Job is created if {Job.Field} {Job.Operator} {Job.Value} then {Job.Action}")
                else:
                    conn.execute(
                        self.peerJobTable.update().values({
                            "Field": Job.Field,
                            "Operator": Job.Operator,
                            "Value": Job.Value,
                            "Action": Job.Action
                        }).where(self.peerJobTable.columns.JobID == Job.JobID)
                    )
                    self.JobLogger.log(Job.JobID, Message=f"Job is updated from if {currentJob[0].Field} {currentJob[0].Operator} {currentJob[0].Value} then {currentJob[0].Action}; to if {Job.Field} {Job.Operator} {Job.Value} then {Job.Action}")
            self.__getJobs()
            self.WireguardConfigurations.get(Job.Configuration).searchPeer(Job.Peer)[1].getJobs()
            return True, list(
                filter(lambda x: x.Configuration == Job.Configuration and x.Peer == Job.Peer and x.JobID == Job.JobID,
                       self.Jobs))
        except Exception as e:
            traceback.print_exc()
            return False, str(e)

    def deleteJob(self, Job: PeerJob) -> tuple[bool, None] | tuple[bool, str]:
        try:
            if len(self.searchJobById(Job.JobID)) == 0:
                return False, "Job does not exist"
            with self.engine.begin() as conn:
                conn.execute(
                    self.peerJobTable.update().values(
                        {
                            "ExpireDate": datetime.now()
                        }
                    ).where(self.peerJobTable.columns.JobID == Job.JobID)
                )
                self.JobLogger.log(Job.JobID, Message=f"Job is removed due to being deleted or finished.")
            self.__getJobs()
            self.WireguardConfigurations.get(Job.Configuration).searchPeer(Job.Peer)[1].getJobs()
            return True, None
        except Exception as e:
            return False, str(e)

    def updateJobConfigurationName(self, ConfigurationName: str, NewConfigurationName: str) -> tuple[bool, str] | tuple[bool, None]:
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    self.peerJobTable.update().values({
                        "Configuration": NewConfigurationName
                    }).where(self.peerJobTable.columns.Configuration == ConfigurationName)
                )
            self.__getJobs()
            return True, None
        except Exception as e:
            return False, str(e)
    
    def getPeerJobLogs(self, configurationName):
        return self.JobLogger.getLogs(configurationName)

    def runJob(self):
        current_app.logger.info("Running scheduled jobs")
        needToDelete = []
        self.__getJobs()
        for job in self.Jobs:
            try:
                c = self.WireguardConfigurations.get(job.Configuration)
                if c is not None:
                    f, fp = c.searchPeer(job.Peer)
                    if f:
                        runAction = False
                        
                        # Handle data usage fields (these are numeric)
                        if job.Field in ["total_receive", "total_sent", "total_data"]:
                            s = job.Field.split("_")[1]
                            x = getattr(fp, f"total_{s}", 0) + getattr(fp, f"cumu_{s}", 0)
                            try:
                                y = float(job.Value)
                                runAction = self.__runJob_Compare(x, y, job.Operator)
                            except ValueError:
                                current_app.logger.error(f"Invalid numeric value for job {job.JobID}: {job.Value}")
                                self.JobLogger.log(job.JobID, False, f"Invalid numeric value: {job.Value}")
                                continue
                        
                        # Try to determine if the value is a datetime by attempting to parse it
                        else:
                            # First, try to parse job.Value as a datetime
                            is_datetime_comparison = False
                            try:
                                y_datetime = datetime.strptime(job.Value, "%Y-%m-%d %H:%M:%S")
                                # If parsing succeeded, this is likely a datetime comparison
                                is_datetime_comparison = True
                                x = datetime.now()
                                runAction = self.__runJob_Compare(x, y_datetime, job.Operator)
                            except ValueError:
                                # Not a datetime, treat as string comparison
                                pass
                            
                            if not is_datetime_comparison:
                                # Handle as string/other type comparison
                                # Try to get the field value from the peer object
                                if hasattr(fp, job.Field):
                                    peer_value = getattr(fp, job.Field)
                                    # Convert both to strings for comparison
                                    runAction = self.__runJob_Compare(str(peer_value), str(job.Value), job.Operator)
                                else:
                                    current_app.logger.warning(f"Field '{job.Field}' not found on peer object for job {job.JobID}")
                                    self.JobLogger.log(job.JobID, False, f"Field '{job.Field}' not found on peer object")
                                    continue

                        if runAction:
                            s = False
                            msg = ""
                            if job.Action == "restrict":
                                # Pass self as AllPeerJobs and the stored AllPeerShareLinks
                                s, msg = c.restrictPeers([fp.id], self, self.AllPeerShareLinks)
                            elif job.Action == "delete":
                                # Pass self as AllPeerJobs and the stored AllPeerShareLinks
                                s, msg = c.deletePeers([fp.id], self, self.AllPeerShareLinks)
                            elif job.Action == "reset_total_data_usage":
                                s = fp.resetDataUsage("total")
                                # These might also need the additional arguments
                                c.restrictPeers([fp.id], self, self.AllPeerShareLinks)
                                c.allowAccessPeers([fp.id], self, self.AllPeerShareLinks)
                                msg = "Data usage reset"
                            
                            if s is True:
                                self.JobLogger.log(job.JobID, s,
                                              f"Peer {fp.id} from {c.Name} is successfully {job.Action}ed."
                                              )
                                current_app.logger.info(f"Peer {fp.id} from {c.Name} is successfully {job.Action}ed.")
                                needToDelete.append(job)
                            else:
                                current_app.logger.info(f"Peer {fp.id} from {c.Name} failed to {job.Action}. Reason: {msg}")
                                self.JobLogger.log(job.JobID, s,
                                              f"Peer {fp.id} from {c.Name} failed to {job.Action}. Reason: {msg}"
                                              )
                    else:
                        current_app.logger.warning(f"Can't find peer {job.Peer} in configuration {c.Name}")
                        self.JobLogger.log(job.JobID, False,
                                      f"Can't find peer {job.Peer} in configuration {c.Name}"
                                      )
                else:
                    current_app.logger.warning(f"Can't find configuration {job.Configuration}")
                    self.JobLogger.log(job.JobID, False,
                                  f"Can't find configuration {job.Configuration}"
                                  )
            except Exception as e:
                current_app.logger.error(f"Error processing job {job.JobID}: {str(e)}")
                self.JobLogger.log(job.JobID, False, f"Error processing job: {str(e)}")
                
        for j in needToDelete:
            self.deleteJob(j)

    def __runJob_Compare(self, x, y, operator: str):
        """
        Compare two values based on the operator.
        Handles float, datetime, and string comparisons.
        """
        try:
            if operator == "eq":
                return x == y
            if operator == "neq":
                return x != y
            if operator == "lgt":
                return x > y
            if operator == "lst":
                return x < y
        except TypeError:
            # If comparison fails (e.g., comparing incompatible types), 
            # try string comparison
            return self.__runJob_Compare(str(x), str(y), operator)
        return False
