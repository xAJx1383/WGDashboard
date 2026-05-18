<script setup>
import { ref, onMounted } from 'vue'

const status = ref(null)
const jobs = ref([])
const error = ref(null)
const loading = ref(true)

const fetchData = async () => {
  try {
    const statusRes = await fetch('/api/status')
    if (!statusRes.ok) {
      if (statusRes.status === 403) {
        throw new Error("Access Denied. You are not connected via WireGuard or not recognized as a peer.")
      }
      throw new Error(`Failed to fetch status: ${statusRes.statusText}`)
    }
    const statusData = await statusRes.json()
    status.value = statusData.data

    const jobsRes = await fetch('/api/jobs')
    if (jobsRes.ok) {
      const jobsData = await jobsRes.json()
      jobs.value = jobsData.data
    }
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="container py-5" data-bs-theme="dark">
    <div class="row justify-content-center">
      <div class="col-lg-8 col-md-10">
        
        <!-- Header -->
        <div class="text-center mb-5">
          <img src="/img/Logo-2-Rounded-512x512.png" alt="WGDashboard Logo" style="width: 80px; height: 80px;" class="mb-3">
          <h2 class="fw-bold">Peer Portal</h2>
          <p class="text-muted">View your connection status and usage</p>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="alert alert-danger shadow-sm rounded-4 border-0" role="alert">
          <div class="d-flex align-items-center">
            <i class="bi bi-exclamation-triangle-fill fs-4 me-3"></i>
            <div>
              <h5 class="alert-heading mb-1">Access Error</h5>
              <p class="mb-0">{{ error }}</p>
            </div>
          </div>
        </div>

        <!-- Content State -->
        <div v-else>
          <!-- Status Card -->
          <div class="card shadow-sm rounded-4 border-0 mb-4 bg-dark text-light">
            <div class="card-header bg-transparent border-bottom border-secondary pt-4 pb-3 px-4">
              <div class="d-flex align-items-center justify-content-between">
                <h5 class="mb-0 fw-bold">
                  <i class="bi bi-person-badge text-primary me-2"></i>
                  {{ status.peer.name }}
                </h5>
                <span class="badge rounded-pill px-3 py-2" :class="status.peer.status === 'running' ? 'text-bg-success' : 'text-bg-secondary'">
                  <i class="bi me-1" :class="status.peer.status === 'running' ? 'bi-check-circle-fill' : 'bi-dash-circle-fill'"></i>
                  {{ status.peer.status === 'running' ? 'Connected' : 'Offline' }}
                </span>
              </div>
            </div>
            <div class="card-body p-4">
              <div class="row g-4">
                <div class="col-sm-6">
                  <div class="text-secondary small mb-1">Public Key</div>
                  <div class="font-monospace small text-truncate" :title="status.peer.id">{{ status.peer.id }}</div>
                </div>
                <div class="col-sm-6">
                  <div class="text-secondary small mb-1">Allowed IPs</div>
                  <div class="font-monospace small">{{ status.peer.allowed_ip }}</div>
                </div>
                <div class="col-sm-6">
                  <div class="text-secondary small mb-1">Latest Handshake</div>
                  <div>{{ status.peer.latest_handshake !== 'No Handshake' ? status.peer.latest_handshake + ' ago' : 'Never' }}</div>
                </div>
                <div class="col-sm-6">
                  <div class="text-secondary small mb-1">Endpoint</div>
                  <div class="font-monospace small">{{ status.peer.endpoint || 'N/A' }}</div>
                </div>
              </div>

              <hr class="border-secondary my-4">

              <!-- Usage Stats -->
              <h6 class="fw-bold mb-3">Traffic Usage</h6>
              <div class="row g-3">
                <div class="col-sm-4">
                  <div class="p-3 rounded-3 bg-body-tertiary border border-secondary-subtle">
                    <div class="d-flex align-items-center mb-2">
                      <i class="bi bi-arrow-down-circle-fill text-primary me-2"></i>
                      <span class="text-secondary small fw-medium">Downloaded</span>
                    </div>
                    <h5 class="mb-0 fw-bold">{{ status.peer.total_receive_formatted }}</h5>
                  </div>
                </div>
                <div class="col-sm-4">
                  <div class="p-3 rounded-3 bg-body-tertiary border border-secondary-subtle">
                    <div class="d-flex align-items-center mb-2">
                      <i class="bi bi-arrow-up-circle-fill text-success me-2"></i>
                      <span class="text-secondary small fw-medium">Uploaded</span>
                    </div>
                    <h5 class="mb-0 fw-bold">{{ status.peer.total_sent_formatted }}</h5>
                  </div>
                </div>
                <div class="col-sm-4">
                  <div class="p-3 rounded-3 bg-body-tertiary border border-secondary-subtle">
                    <div class="d-flex align-items-center mb-2">
                      <i class="bi bi-arrow-down-up text-secondary me-2"></i>
                      <span class="text-secondary small fw-medium">Total</span>
                    </div>
                    <h5 class="mb-0 fw-bold">{{ status.peer.total_data_formatted }}</h5>
                  </div>
                </div>
              </div>
              
              <div v-if="status.peer.restricted" class="mt-4 alert alert-warning mb-0 border-0 rounded-3 d-flex align-items-center py-2">
                <i class="bi bi-lock-fill me-2 fs-5"></i>
                <small class="fw-medium">Your access is currently restricted.</small>
              </div>
            </div>
          </div>

          <!-- Active Jobs Card -->
          <div class="card shadow-sm rounded-4 border-0 bg-dark text-light">
            <div class="card-header bg-transparent border-bottom border-secondary pt-4 pb-3 px-4">
              <h5 class="mb-0 fw-bold">
                <i class="bi bi-robot text-info me-2"></i>
                Active Rules
              </h5>
            </div>
            <div class="card-body p-0">
              <div v-if="jobs.length === 0" class="text-center py-5 text-secondary">
                <i class="bi bi-shield-check fs-2 mb-2 d-block text-muted"></i>
                No active limits or rules for your connection.
              </div>
              <ul v-else class="list-group list-group-flush rounded-bottom-4">
                <li v-for="job in jobs" :key="job.id" class="list-group-item bg-transparent text-light px-4 py-3 border-secondary">
                  <div class="d-flex align-items-start">
                    <i class="bi bi-info-circle text-info mt-1 me-3"></i>
                    <div>
                      <div class="fw-medium">{{ job.description }}</div>
                      <small class="text-secondary">Added on {{ job.created }}</small>
                    </div>
                  </div>
                </li>
              </ul>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<style>
body {
  background-color: #212529; /* bs-dark */
  color: #f8f9fa;
}
</style>
