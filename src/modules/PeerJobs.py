"""
Peer Jobs
"""
from .ConnectionString import ConnectionString
from .PeerJob import PeerJob
from .PeerJobLogger import PeerJobLogger
import sqlalchemy as db
from datetime import datetime
from flask import current_app
import os

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
    
    def dumpJobsForConfiguration(self, configurationName: str) -> list[str]:
        """
        Dumps all active jobs for a given configuration as a list of SQL INSERT statements.
        """
        job_lines = []
        with self.engine.connect() as conn:
            jobs_for_config = conn.execute(
                self.peerJobTable.select().where(
                    self.peerJobTable.columns.Configuration == configurationName,
                    self.peerJobTable.columns.ExpireDate.is_(None)
                )
            ).mappings().fetchall()

            for job_row in jobs_for_config:
                insert_stmt = self.peerJobTable.insert().values(dict(job_row))
                job_lines.append(
                    str(insert_stmt.compile(compile_kwargs={"literal_binds": True})) + ";"
                )
        return job_lines

    def getPeerJobLogs(self, configurationName):
        return self.JobLogger.getLogs(configurationName)

    def runJob(self):
        current_app.logger.info("Running scheduled jobs")
        needToDelete = []
        self.__getJobs()
        
        # EMERGENCY: Log all jobs to understand what's happening
        for job in self.Jobs:
            current_app.logger.warning(f"Active Job: ID={job.JobID}, Peer={job.Peer}, Field={job.Field}, Operator={job.Operator}, Value={job.Value}, Action={job.Action}")
        
        for job in self.Jobs:
            try:
                c = self.WireguardConfigurations.get(job.Configuration)
                if c is not None:
                    f, fp = c.searchPeer(job.Peer)
                    if f and fp is not None:
                        runAction = False
                        
                        # Log what we're comparing BEFORE the comparison
                        current_app.logger.warning(f"Evaluating job {job.JobID} for peer {fp.id}: Field={job.Field}, Operator={job.Operator}, Value={job.Value}")
                        
                        # Handle data usage fields (these are numeric)
                        if job.Field in ["total_receive", "total_sent", "total_data"]:
                            s = job.Field.split("_")[1]
                            x = getattr(fp, f"total_{s}", 0) + getattr(fp, f"cumu_{s}", 0)
                            try:
                                y = float(job.Value)
                                runAction = self.__runJob_Compare(x, y, job.Operator)
                                current_app.logger.warning(f"Data comparison result: {x} {job.Operator} {y} = {runAction}")
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
                                current_app.logger.warning(f"DateTime comparison result: {x} {job.Operator} {y_datetime} = {runAction}")
                            except ValueError:
                                # Not a datetime, treat as string comparison
                                pass
                            
                            # if not is_datetime_comparison:
                            #     # Handle as string/other type comparison
                            #     # Try to get the field value from the peer object
                            #     if hasattr(fp, job.Field):
                            #         peer_value = getattr(fp, job.Field)
                            #         # Convert both to strings for comparison
                            #         current_app.logger.warning(f"String comparison for field '{job.Field}': peer_value='{peer_value}' {job.Operator} job_value='{job.Value}'")
                            #         runAction = self.__runJob_Compare(str(peer_value), str(job.Value), job.Operator)
                            #         current_app.logger.warning(f"String comparison result: '{peer_value}' {job.Operator} '{job.Value}' = {runAction}")
                            #     else:
                            #         current_app.logger.warning(f"Field '{job.Field}' not found on peer object for job {job.JobID}")
                            #         self.JobLogger.log(job.JobID, False, f"Field '{job.Field}' not found on peer object")
                            #         continue

                        if runAction:
                            # EMERGENCY FIX: DISABLE ALL DESTRUCTIVE ACTIONS
                            # current_app.logger.error(f"!!! EMERGENCY: Job {job.JobID} would perform '{job.Action}' on peer {fp.id} - ACTION BLOCKED FOR SAFETY !!!")
                            # current_app.logger.error(f"!!! Job details: Field={job.Field}, Operator={job.Operator}, Value={job.Value}")
                            
                            # DO NOT EXECUTE ANY ACTIONS - JUST LOG
                            # Comment out all action execution until we understand why jobs are triggering
                            
                            s = False
                            msg = ""
                            if job.Action == "restrict":
                                s, msg = c.restrictPeers([fp.id], self, self.AllPeerShareLinks)
                            elif job.Action == "delete":
                                s, msg = c.deletePeers([fp.id], self, self.AllPeerShareLinks)
                            elif job.Action == "reset_total_data_usage":
                                s = fp.resetDataUsage("total")
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

    def importJobsFromFile(self, sql_path: str, merge: bool = True) -> tuple[bool, str]:
        """
        Read a .jobs.sql file (created by dumpJobsForConfiguration) and execute each INSERT line.
        If merge=True, skip INSERTs whose JobID already exists.
        Returns (True, None) on success or (False, "error message") on failure.
        """
        import os
        from sqlalchemy import text

        if not os.path.exists(sql_path):
            return False, "jobs SQL file not found"

        try:
            with open(sql_path, 'r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]

            if not lines:
                return True, None  # nothing to do

            with self.engine.begin() as conn:
                for line in lines:
                    # Only handle INSERT lines (our dump writes one INSERT per line)
                    if not line.upper().startswith('INSERT'):
                        continue

                    # Optionally check JobID presence and skip if exists
                    if merge:
                        # attempt to parse JobID value quickly (works for our dumped format)
                        import re
                        m = re.search(r"VALUES\s*\((.*)\);?$", line, flags=re.IGNORECASE)
                        if m:
                            vals_raw = m.group(1)
                            # split on commas outside quotes (simple)
                            vals = []
                            cur = ''
                            in_q = False
                            for ch in vals_raw:
                                if ch == "'" and not in_q:
                                    in_q = True
                                    cur += ch
                                elif ch == "'" and in_q:
                                    cur += ch
                                    in_q = False
                                elif ch == ',' and not in_q:
                                    vals.append(cur.strip())
                                    cur = ''
                                else:
                                    cur += ch
                            if cur.strip() != '':
                                vals.append(cur.strip())
                            # JobID is first column in our dump
                            if len(vals) > 0:
                                jobid_val = vals[0].strip()
                                if jobid_val.upper() == 'NULL':
                                    jobid = None
                                else:
                                    if jobid_val.startswith("'") and jobid_val.endswith("'"):
                                        jobid = jobid_val[1:-1].replace("''", "'")
                                    else:
                                        jobid = jobid_val
                                if jobid:
                                    exists = conn.execute(
                                        self.peerJobTable.select().where(self.peerJobTable.c.JobID == jobid)
                                    ).first()
                                    if exists:
                                        # skip this insert to avoid duplicate JobID
                                        continue
                    # execute the INSERT
                    try:
                        conn.execute(text(line))
                    except Exception as e:
                        # return the error to caller so it can be logged
                        return False, f"Error executing line: {line[:200]}... Error: {str(e)}"
            try:
                self.__getJobs()
            except Exception:
                # don't break restore if reload somehow fails; return success but log if needed
                pass

            return True, None
        except Exception as e:
            return False, str(e)
