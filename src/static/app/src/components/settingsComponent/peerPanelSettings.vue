<script setup lang="ts">
import {DashboardConfigurationStore} from "@/stores/DashboardConfigurationStore.js";
import LocaleText from "@/components/text/localeText.vue";
import {fetchPost} from "@/utilities/fetch.js";
import {ref, watch, onMounted} from "vue";

const store = DashboardConfigurationStore()

const peerPanelEnable = ref(false)
const peerPanelPort = ref("10087")
const peerPanelBindAddress = ref("0.0.0.0")

const invalidFeedbackPort = ref("")
const showInvalidFeedbackPort = ref(false)
const isValidPort = ref(false)
const timeoutPort = ref(undefined)
const changedPort = ref(false)
const updatingPort = ref(false)

const invalidFeedbackBind = ref("")
const showInvalidFeedbackBind = ref(false)
const isValidBind = ref(false)
const timeoutBind = ref(undefined)
const changedBind = ref(false)
const updatingBind = ref(false)

onMounted(() => {
    peerPanelEnable.value = store.Configuration.PeerPanel.peer_panel_enable === 'true' || store.Configuration.PeerPanel.peer_panel_enable === true;
    peerPanelPort.value = store.Configuration.PeerPanel.peer_panel_port;
    peerPanelBindAddress.value = store.Configuration.PeerPanel.peer_panel_bind_address;
})

const updateToggle = async () => {
    const value = peerPanelEnable.value ? "true" : "false"
    await fetchPost("/api/updateDashboardConfigurationItem", {
        section: "PeerPanel",
        key: "peer_panel_enable",
        value: value
    }, (res) => {
        if (res.status){
            store.Configuration.PeerPanel.peer_panel_enable = value;
        }else{
            peerPanelEnable.value = !peerPanelEnable.value;
        }
    })
}

const useValidationPort = async (e) => {
    if (changedPort.value){
        updatingPort.value = true
        await fetchPost("/api/updateDashboardConfigurationItem", {
            section: "PeerPanel",
            key: "peer_panel_port",
            value: peerPanelPort.value
        }, (res) => {
            if (res.status){
                e.target.classList.add("is-valid")
                showInvalidFeedbackPort.value = false;
                store.Configuration.PeerPanel.peer_panel_port = peerPanelPort.value
                clearTimeout(timeoutPort.value)
                timeoutPort.value = setTimeout(() => {
                    e.target.classList.remove("is-valid")
                }, 5000);
            }else{
                isValidPort.value = false;
                showInvalidFeedbackPort.value = true;
                invalidFeedbackPort.value = res.message
            }
            changedPort.value = false
            updatingPort.value = false;
        })
    }
}

const useValidationBind = async (e) => {
    if (changedBind.value){
        updatingBind.value = true
        await fetchPost("/api/updateDashboardConfigurationItem", {
            section: "PeerPanel",
            key: "peer_panel_bind_address",
            value: peerPanelBindAddress.value
        }, (res) => {
            if (res.status){
                e.target.classList.add("is-valid")
                showInvalidFeedbackBind.value = false;
                store.Configuration.PeerPanel.peer_panel_bind_address = peerPanelBindAddress.value
                clearTimeout(timeoutBind.value)
                timeoutBind.value = setTimeout(() => {
                    e.target.classList.remove("is-valid")
                }, 5000);
            }else{
                isValidBind.value = false;
                showInvalidFeedbackBind.value = true;
                invalidFeedbackBind.value = res.message
            }
            changedBind.value = false
            updatingBind.value = false;
        })
    }
}
</script>

<template>
    <div class="card rounded-3">
        <div class="card-header">
            <h6 class="my-2">
                <i class="bi bi-person-badge-fill me-2"></i>
                <LocaleText t="Peer Panel"></LocaleText>
            </h6>
        </div>
        <div class="card-body">
            <div class="form-check form-switch mb-3">
                <input class="form-check-input" type="checkbox" role="switch" id="peerPanelEnable" 
                       v-model="peerPanelEnable" @change="updateToggle">
                <label class="form-check-label" for="peerPanelEnable">
                    <strong><LocaleText t="Enable Peer Panel"></LocaleText></strong>
                    <br>
                    <small class="text-muted"><LocaleText t="Allow peers to view their own usage and active jobs by accessing a separate panel"></LocaleText></small>
                </label>
            </div>
            
            <div class="row g-2" v-if="peerPanelEnable">
                <div class="col-sm">
                    <div class="form-group">
                        <label for="input_peer_panel_bind" class="text-muted mb-1">
                            <strong><small>
                                <LocaleText t="Bind Address"></LocaleText>
                            </small></strong>
                        </label>
                        <input type="text" class="form-control"
                               :class="{'is-invalid': showInvalidFeedbackBind, 'is-valid': isValidBind}"
                               id="input_peer_panel_bind"
                               v-model="peerPanelBindAddress"
                               @keydown="changedBind = true"
                               @blur="useValidationBind($event)"
                               :disabled="updatingBind"
                        >
                        <div class="invalid-feedback">{{invalidFeedbackBind}}</div>
                    </div>
                </div>
                <div class="col-sm">
                    <div class="form-group">
                        <label for="input_peer_panel_port" class="text-muted mb-1">
                            <strong><small>
                                <LocaleText t="Listen Port"></LocaleText>
                            </small></strong>
                        </label>
                        <input type="number" class="form-control"
                               :class="{'is-invalid': showInvalidFeedbackPort, 'is-valid': isValidPort}"
                               id="input_peer_panel_port"
                               v-model="peerPanelPort"
                               @keydown="changedPort = true"
                               @blur="useValidationPort($event)"
                               :disabled="updatingPort"
                        >
                        <div class="invalid-feedback">{{invalidFeedbackPort}}</div>
                    </div>
                </div>
            </div>
            <div v-if="peerPanelEnable"
                class="px-2 py-1 text-warning-emphasis bg-warning-subtle border border-warning-subtle rounded-2 d-inline-block mb-2 mt-2">
                <small><i class="bi bi-exclamation-triangle-fill me-2"></i>
                    <LocaleText t="Manual restart of WGDashboard is needed to apply changes to Peer Panel settings"></LocaleText>
                </small>
            </div>
        </div>
    </div>
</template>

<style scoped>

</style>
