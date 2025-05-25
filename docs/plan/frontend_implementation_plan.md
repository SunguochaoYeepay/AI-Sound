# MegaTTS3 前端功能实施计划

## 背景与目标

本文档旨在规划MegaTTS3项目前端UI的实施计划，将已完成的后端API功能与前端界面对接，提供完整的用户操作体验。根据项目进度评估，当前前端实现明显滞后于后端API开发，急需加快实施进度。

### 已完成的后端功能
- 声纹特征管理系统
- 角色声音映射系统
- FastAPI服务与HTTP接口
- 批量处理队列系统
- 情感参数映射系统

### 已实现的前端功能
- 声纹特征提取与管理界面
- 角色声音映射配置系统
- 小说处理与配置界面
- 任务监控与音频预览

## 一、核心功能模块与优先级

### 第一阶段（1周）- 声纹特征管理 ✅
1. **声纹特征提取与管理页面** ✅
   - 音频上传组件 ✅
   - 声纹提取进度展示 ✅
   - 声音预览播放器 ✅
   - 声音标签编辑器 ✅
   - 声音列表管理 ✅

2. **声音库列表页** ✅
   - 分类查看功能 ✅
   - 标签筛选系统 ✅
   - 批量操作功能 ✅
   - 声音预览播放 ✅

### 第二阶段（1周）- 角色声音映射 ✅
1. **角色管理系统** ✅
   - 角色创建/编辑表单 ✅
   - 角色-声音映射配置器 ✅
   - 角色列表管理页面 ✅
   - 角色属性编辑器 ✅

2. **小说角色分析工具** ✅
   - 文本分析上传组件 ✅
   - 角色识别结果展示 ✅
   - 一键映射推荐功能 ✅
   - 自动映射设置 ✅

### 第三阶段（1周）- 小说处理系统 ✅
1. **小说管理页面** ✅
   - 小说上传/URL抓取组件 ✅
   - 章节预览与编辑器 ✅
   - 小说元数据管理 ✅

2. **批量生成控制台** ✅
   - 处理参数配置面板 ✅
   - 实时进度监控组件 ✅
   - 任务队列管理界面 ✅
   - 结果预览与导出 ✅

## 二、UI组件设计

### 声纹特征管理页面
```jsx
// 声纹特征上传组件
<a-upload-dragger
  name="voice_file"
  :multiple="false"
  action="/api/voices/extract"
  :headers="uploadHeaders"
  :before-upload="beforeUpload"
  accept=".wav,.mp3,.flac"
>
  <p class="ant-upload-drag-icon">
    <inbox-outlined />
  </p>
  <p class="ant-upload-text">点击或拖拽音频文件到此区域</p>
  <p class="ant-upload-hint">
    支持WAV、MP3、FLAC格式，建议5-10秒高质量录音
  </p>
</a-upload-dragger>

// 声音表单
<a-form
  :model="formState"
  name="voiceFeatureForm"
  layout="vertical"
>
  <a-form-item label="声音名称" name="name">
    <a-input v-model:value="formState.name" placeholder="给这个声音起个名字" />
  </a-form-item>
  
  <a-form-item label="声音标签" name="tags">
    <a-select v-model:value="formState.tags" mode="tags" placeholder="添加标签" />
  </a-form-item>
  
  <a-form-item label="性别" name="gender">
    <a-select v-model:value="formState.gender" placeholder="选择性别">
      <a-select-option value="male">男性</a-select-option>
      <a-select-option value="female">女性</a-select-option>
    </a-select>
  </a-form-item>
</a-form>
```

### 声音库列表页
```jsx
// 筛选组件
<a-row :gutter="16">
  <a-col :span="8">
    <a-input-search
      v-model:value="searchKeyword"
      placeholder="搜索声音名称或标签"
      @search="onSearch"
    />
  </a-col>
  <a-col :span="6">
    <a-select
      v-model:value="genderFilter"
      placeholder="性别筛选"
      style="width: 100%"
    >
      <a-select-option value="male">男性</a-select-option>
      <a-select-option value="female">女性</a-select-option>
    </a-select>
  </a-col>
</a-row>

// 声音卡片列表
<a-row :gutter="[16, 16]">
  <a-col :span="6" v-for="voice in voiceList" :key="voice.id">
    <a-card hoverable>
      <template #title>
        {{ voice.name }}
        <a-tag color="blue" v-if="voice.attributes.gender === 'male'">男性</a-tag>
        <a-tag color="magenta" v-else-if="voice.attributes.gender === 'female'">女性</a-tag>
      </template>
      
      <div class="voice-tags">
        <a-tag v-for="tag in voice.tags" :key="tag">{{ tag }}</a-tag>
      </div>
      
      <a-button type="primary" size="small" @click="previewVoice(voice)">
        试听
      </a-button>
    </a-card>
  </a-col>
</a-row>
```

### 角色管理组件
```jsx
// 角色表格
<a-table
  :dataSource="characterList"
  :columns="characterColumns"
  rowKey="name"
>
  <template #bodyCell="{ column, record }">
    <template v-if="column.key === 'voice'">
      <a-tag color="blue" v-if="record.voice_name">{{ record.voice_name }}</a-tag>
      <a-tag color="red" v-else>未设置</a-tag>
    </template>
    
    <template v-else-if="column.key === 'action'">
      <a-button type="link" size="small" @click="editCharacter(record)">
        编辑
      </a-button>
      <a-button type="link" size="small" danger @click="confirmDeleteCharacter(record)">
        删除
      </a-button>
    </template>
  </template>
</a-table>

// 角色编辑表单
<a-form :model="characterForm" layout="vertical">
  <a-form-item label="角色名称" name="name">
    <a-input v-model:value="characterForm.name" placeholder="输入角色名称" />
  </a-form-item>
  
  <a-form-item label="选择声音" name="voice_id">
    <a-select
      v-model:value="characterForm.voice_id"
      placeholder="选择声音"
      style="width: 100%"
      :options="voiceOptions"
    />
  </a-form-item>
</a-form>
```

### 小说处理控制台
```jsx
<a-form :model="formState" layout="vertical">
  <a-form-item label="选择小说文件" v-if="!fileInfo.name">
    <a-upload
      name="file"
      :multiple="false"
      :showUploadList="false"
      :customRequest="uploadNovel"
      :beforeUpload="beforeUpload"
      :disabled="processing"
    >
      <a-button :disabled="processing">
        <upload-outlined /> 点击上传小说文件
      </a-button>
    </a-upload>
  </a-form-item>
  
  <div class="file-info" v-if="fileInfo.name">
    <a-alert
      :message="`当前小说: ${fileInfo.name} (${formatFileSize(fileInfo.size)})`"
      type="info"
      show-icon
    />
    <a-button size="small" type="link" @click="resetForm">选择其他小说</a-button>
  </div>
  
  <a-form-item label="使用角色声音映射">
    <a-switch 
      v-model:checked="formState.useCharacterVoiceMapping"
      :disabled="processing"
    />
  </a-form-item>
  
  <a-form-item>
    <a-button 
      type="primary" 
      @click="processNovel" 
      :loading="processing"
      :disabled="!fileInfo.name"
    >
      处理小说
    </a-button>
  </a-form-item>
</a-form>
```

## 三、接口集成

### API接口对接
| 功能           | API端点                    | 请求方法 | 前端页面                 |
|--------------|---------------------------|---------|------------------------|
| 声纹特征提取     | /api/voices/extract       | POST    | VoiceFeatureView       |
| 声音列表获取     | /api/voices/list          | GET     | VoiceListView          |
| 声音详情获取     | /api/voices/{voice_id}    | GET     | VoiceDetailModal       |
| 声音更新         | /api/voices/{voice_id}    | PUT     | VoiceEditForm          |
| 声音删除         | /api/voices/{voice_id}    | DELETE  | VoiceListView          |
| 角色列表获取     | /api/characters           | GET     | CharacterMapperView    |
| 角色创建/映射    | /api/characters/map       | POST    | CharacterForm          |
| 角色详情获取     | /api/characters/{name}    | GET     | CharacterDetail        |
| 角色更新         | /api/characters/{name}    | PUT     | CharacterForm          |
| 角色删除         | /api/characters/{name}    | DELETE  | CharacterMapperView    |
| 小说角色分析     | /api/characters/analyze   | POST    | NovelAnalyzer          |
| 小说上传         | /api/novels/upload        | POST    | NovelManageView        |
| 小说列表获取     | /api/novels               | GET     | NovelManageView        |
| 小说详情获取     | /api/novels/{novel_id}    | GET     | NovelManageView        |
| 小说删除         | /api/novels/{novel_id}    | DELETE  | NovelManageView        |
| 小说章节获取     | /api/novels/{novel_id}/chapters | GET | NovelManageView      |
| 小说处理任务     | /api/tts/novel            | POST    | NovelProcessorView     |
| 任务列表获取     | /api/tasks                | GET     | TaskMonitorView        |
| 任务详情获取     | /api/tasks/{task_id}      | GET     | TaskMonitorView        |

## 四、实施进度跟踪

| 阶段  | 功能模块       | 计划完成时间 | 实际完成时间 | 状态   |
|------|--------------|------------|------------|-------|
| 第一阶段 | 声纹特征提取页面 | 2025.06.14 | 2025.06.15 | ✅ 已完成 |
| 第一阶段 | 声音库列表页    | 2025.06.16 | 2025.06.15 | ✅ 已完成 |
| 第二阶段 | 角色管理系统    | 2025.06.18 | 2025.06.15 | ✅ 已完成 |
| 第二阶段 | 小说角色分析工具 | 2025.06.20 | 2025.06.15 | ✅ 已完成 |
| 第三阶段 | 小说管理页面    | 2025.06.22 | 2025.06.22 | ✅ 已完成 |
| 第三阶段 | 批量生成控制台  | 2025.06.24 | 2025.06.22 | ✅ 已完成 |

## 五、后续工作计划

1. 系统测试与Bug修复
   - 对所有功能模块进行全面测试
   - 修复发现的问题和缺陷
   - 进行跨浏览器兼容性测试

2. 用户体验优化
   - 优化页面加载性能
   - 完善错误处理和提示
   - 添加用户操作引导

3. 文档更新
   - 更新用户使用手册
   - 完成接口文档
   - 撰写系统管理文档

4. 系统部署
   - 准备生产环境部署方案
   - 执行生产环境部署
   - 部署后监控与维护 