<template>
  <div class="admin-fallback">
    <div class="section-header">
      <h2>Fallback 服务配置</h2>
      <p class="subtitle">配置外部 Yggdrasil 或 Mojang API 以支持正版登录与角色回退</p>
    </div>

    <!-- Global Settings -->
    <el-card class="box-card mb-4" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>全局策略</span>
          <el-button type="primary" size="small" @click="saveSettings" :loading="saving">保存所有设置</el-button>
        </div>
      </template>
      <el-form label-position="left" label-width="120px">
        <el-form-item label="回退策略">
          <el-radio-group v-model="settings.fallback_strategy">
            <el-radio-button label="serial">顺序尝试</el-radio-button>
            <el-radio-button label="parallel">并发尝试</el-radio-button>
          </el-radio-group>
          <span class="setting-desc ml-4">顺序尝试按优先级逐个回退；并发尝试则同时请求所有可用端点。</span>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Endpoints Table -->
    <el-card class="box-card mb-4" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>Fallback 端点列表</span>
          <el-button size="small" @click="addFallback" :icon="Plus">新增端点</el-button>
        </div>
      </template>

      <el-table 
        :data="fallbacks" 
        style="width: 100%" 
        row-key="rowKey"
        @expand-change="handleExpandChange"
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="endpoint-expanded-content">
              <!-- Endpoint Config -->
              <div class="config-grid mb-4">
                <div class="grid-item">
                  <div class="label">Session URL</div>
                  <el-input v-model="row.session_url" size="small" placeholder="https://..." />
                </div>
                <div class="grid-item">
                  <div class="label">Account URL</div>
                  <el-input v-model="row.account_url" size="small" placeholder="https://..." />
                </div>
                <div class="grid-item">
                  <div class="label">Services URL</div>
                  <el-input v-model="row.services_url" size="small" placeholder="https://..." />
                </div>
                <div class="grid-item">
                  <div class="label">Skin Domains</div>
                  <el-input v-model="row.skin_domains_text" size="small" placeholder="textures.minecraft.net" />
                </div>
              </div>

              <!-- Functional Switches -->
              <div class="switches-section">
                <div class="setting-item">
                  <el-switch v-model="row.enable_profile" />
                  <div class="text">
                    <span class="name">转发 Profile 请求</span>
                    <span class="desc">查无此人时，尝试向此端点查询角色信息</span>
                  </div>
                </div>
                <div class="setting-item">
                  <el-switch v-model="row.enable_hasjoined" />
                  <div class="text">
                    <span class="name">转发 HasJoined 验证</span>
                    <span class="desc">本地验证失败时，尝试向此端点验证会话 (支持正版登录)</span>
                  </div>
                </div>
                <div class="setting-item">
                  <el-switch v-model="row.enable_whitelist" @change="(val) => onWhitelistToggle(row, val)" />
                  <div class="text">
                    <span class="name">启用端点白名单</span>
                    <span class="desc">开启后，仅白名单内的用户会被转发至此端点进行 HasJoined 验证</span>
                  </div>
                </div>
              </div>

              <!-- Inline Whitelist -->
              <div v-if="row.enable_whitelist" class="inline-whitelist mt-4">
                <el-divider content-position="left">端点白名单管理</el-divider>
                
                <div v-if="!row.id" class="empty-state">
                  <el-alert title="请先保存设置，保存后即可为此端点添加白名单用户。" type="warning" :closable="false" show-icon />
                </div>
                
                <div v-else class="whitelist-controls">
                  <div class="add-user-bar mb-2">
                    <el-input 
                      v-model="row._new_user" 
                      placeholder="输入正版用户名" 
                      size="small"
                      @keyup.enter="addUser(row)"
                    >
                      <template #append>
                        <el-button @click="addUser(row)" :loading="row._adding">添加</el-button>
                      </template>
                    </el-input>
                  </div>
                  
                  <el-table :data="row._whitelist || []" size="small" border style="width: 100%" max-height="300">
                    <el-table-column prop="username" label="用户名" />
                    <el-table-column prop="created_at" label="添加时间" width="160">
                      <template #default="scope">
                        {{ new Date(scope.row.created_at).toLocaleDateString() }}
                      </template>
                    </el-table-column>
                    <el-table-column label="操作" width="60" align="center">
                      <template #default="scope">
                        <el-button type="danger" :icon="Delete" size="small" @click="removeUser(row, scope.row.username)" link />
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="端点备注 (及优先级)" min-width="200">
          <template #default="scope">
            <div class="note-cell">
              <span class="priority-badge">{{ scope.$index + 1 }}</span>
              <el-input v-model="scope.row.note" size="small" placeholder="例如：Mojang 官方 / 某皮肤站" class="note-input" />
              <div class="status-tags ml-2">
                <el-tag v-if="scope.row.enable_profile" size="small" type="success" effect="plain" class="mini-tag">P</el-tag>
                <el-tag v-if="scope.row.enable_hasjoined" size="small" type="primary" effect="plain" class="mini-tag">A</el-tag>
                <el-tag v-if="scope.row.enable_whitelist" size="small" type="warning" effect="plain" class="mini-tag">W</el-tag>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="缓存 (秒)" width="100">
          <template #default="scope">
            <el-input v-model.number="scope.row.cache_ttl" size="small" />
          </template>
        </el-table-column>

        <el-table-column label="排序与操作" width="180" align="right">
          <template #default="scope">
            <el-button-group>
              <el-button size="small" :icon="ArrowUp" @click="moveUp(scope.$index)" :disabled="scope.$index === 0" />
              <el-button size="small" :icon="ArrowDown" @click="moveDown(scope.$index)" :disabled="scope.$index === fallbacks.length - 1" />
              <el-button size="small" type="danger" :icon="Delete" @click="removeFallback(scope.$index)" />
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, ArrowUp, ArrowDown } from '@element-plus/icons-vue'

const settings = ref({
  fallback_strategy: 'serial'
})
const fallbacks = ref([])
const saving = ref(false)

const jwt = localStorage.getItem('jwt')
const headers = { Authorization: 'Bearer ' + jwt }

// --- Data Fetching ---
async function fetchSettings() {
  try {
    const res = await axios.get('/admin/settings', { headers })
    settings.value.fallback_strategy = res.data.fallback_strategy || 'serial'
    
    const raw = Array.isArray(res.data.fallbacks) ? res.data.fallbacks : []
    fallbacks.value = raw.map((item, index) => {
      return reactive({
        ...item,
        rowKey: item.id || `new_${Date.now()}_${index}`,
        note: item.note || '',
        skin_domains_text: Array.isArray(item.skin_domains) ? item.skin_domains.join(',') : String(item.skin_domains || ''),
        _whitelist: [],
        _new_user: '',
        _adding: false,
        _loaded: false
      })
    })
    fallbacks.value.sort((a, b) => a.priority - b.priority)
  } catch (e) {
    ElMessage.error('无法加载 Fallback 配置')
  }
}

async function saveSettings() {
  saving.value = true
  try {
    const payload = {
      fallback_strategy: settings.value.fallback_strategy,
      fallbacks: fallbacks.value.map(item => ({
        id: item.id,
        priority: item.priority,
        session_url: item.session_url,
        account_url: item.account_url,
        services_url: item.services_url,
        cache_ttl: item.cache_ttl,
        enable_profile: !!item.enable_profile,
        enable_hasjoined: !!item.enable_hasjoined,
        enable_whitelist: !!item.enable_whitelist,
        note: item.note,
        skin_domains: item.skin_domains_text.split(',').map(s => s.trim()).filter(s => s)
      }))
    }
    await axios.post('/admin/settings', payload, { headers })
    ElMessage.success('设置已保存')
    await fetchSettings()
  } catch (e) {
    ElMessage.error('保存设置失败')
  } finally {
    saving.value = false
  }
}

// --- List Management ---
function addFallback() {
  fallbacks.value.push(reactive({
    id: null,
    rowKey: `new_${Date.now()}_${fallbacks.value.length}`,
    priority: fallbacks.value.length + 1,
    session_url: '',
    account_url: '',
    services_url: '',
    cache_ttl: 60,
    enable_profile: true,
    enable_hasjoined: true,
    enable_whitelist: false,
    note: '',
    skin_domains_text: '',
    _whitelist: [],
    _new_user: '',
    _adding: false,
    _loaded: false
  }))
}

function removeFallback(index) {
  fallbacks.value.splice(index, 1)
  syncPriority()
}

function moveUp(index) {
  if (index === 0) return
  const temp = fallbacks.value[index]
  fallbacks.value[index] = fallbacks.value[index - 1]
  fallbacks.value[index - 1] = temp
  syncPriority()
}

function moveDown(index) {
  if (index === fallbacks.value.length - 1) return
  const temp = fallbacks.value[index]
  fallbacks.value[index] = fallbacks.value[index + 1]
  fallbacks.value[index + 1] = temp
  syncPriority()
}

function syncPriority() {
  fallbacks.value.forEach((item, index) => {
    item.priority = index + 1
  })
}

// --- Whitelist Management ---
function handleExpandChange(row, expandedRows) {
  const isExpanded = expandedRows.find(r => r.rowKey === row.rowKey)
  if (isExpanded && row.enable_whitelist && row.id && !row._loaded) {
    fetchWhitelist(row)
  }
}

function onWhitelistToggle(row, val) {
  if (val && row.id && !row._loaded) {
    fetchWhitelist(row)
  }
}

async function fetchWhitelist(row) {
  if (!row.id) return
  try {
    const res = await axios.get('/admin/official-whitelist', {
      headers,
      params: { endpoint_id: row.id }
    })
    row._whitelist = res.data
    row._loaded = true
  } catch (e) {
    ElMessage.error(`加载白名单失败: ${row.note || row.session_url}`)
  }
}

async function addUser(row) {
  if (!row._new_user || !row.id) return
  row._adding = true
  try {
    await axios.post('/admin/official-whitelist', {
      username: row._new_user,
      endpoint_id: row.id
    }, { headers })
    ElMessage.success('用户已添加')
    row._new_user = ''
    await fetchWhitelist(row)
  } catch (e) {
    ElMessage.error('添加失败')
  } finally {
    row._adding = false
  }
}

async function removeUser(row, username) {
  try {
    await ElMessageBox.confirm(`确定要移除 ${username} 吗？`, '警告', { type: 'warning' })
    await axios.delete(`/admin/official-whitelist/${username}`, {
      headers,
      params: { endpoint_id: row.id }
    })
    ElMessage.success('已移除')
    await fetchWhitelist(row)
  } catch (e) {}
}

onMounted(fetchSettings)
</script>

<style scoped>
.admin-fallback {
  max-width: 1200px;
  margin: 0 auto;
}
.section-header { margin-bottom: 24px; }
.section-header h2 { margin: 0 0 4px 0; color: var(--color-heading); }
.subtitle { color: var(--color-text-light); font-size: 14px; }

.box-card { border: 1px solid var(--color-border); background: var(--color-card-background); }
.card-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; }

.setting-desc { font-size: 13px; color: var(--color-text-light); }

.note-cell { display: flex; align-items: center; }
.note-input { flex: 1; }

.priority-badge {
  display: inline-block;
  min-width: 20px;
  height: 20px;
  line-height: 20px;
  text-align: center;
  border-radius: 4px;
  background: var(--color-primary-light-9);
  color: var(--color-primary);
  font-weight: bold;
  font-size: 12px;
  margin-right: 8px;
  padding: 0 4px;
}

.mini-tag {
  padding: 0 4px;
  height: 18px;
  line-height: 16px;
  font-size: 10px;
}

.endpoint-expanded-content {
  padding: 24px 40px;
  background: var(--color-background-soft);
  border-radius: 4px;
}

.config-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.grid-item .label {
  font-size: 12px;
  color: var(--color-text-light);
  margin-bottom: 4px;
}

.switches-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: var(--color-card-background);
  padding: 16px;
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.setting-item {
  display: flex;
  align-items: center;
  gap: 16px;
}
.setting-item .text {
  display: flex;
  flex-direction: column;
}
.setting-item .name { font-weight: 500; font-size: 14px; }
.setting-item .desc { font-size: 12px; color: var(--color-text-light); }

.inline-whitelist {
  background: var(--color-card-background);
  padding: 16px;
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.add-user-bar { max-width: 400px; }

.mb-2 { margin-bottom: 8px; }
.mb-4 { margin-bottom: 16px; }
.mt-4 { margin-top: 16px; }
.ml-2 { margin-left: 8px; }
.ml-4 { margin-left: 16px; }

@media (max-width: 768px) {
  .endpoint-expanded-content { padding: 16px; }
  .config-grid { grid-template-columns: 1fr; }
}
</style>