# 后端API架构重新设计

## 🎯 **API路由结构**

### 1. 书籍结构化API (`/api/books`)
```python
# 书籍章节管理
@router.post("/books/{book_id}/detect-chapters")
async def detect_chapters(book_id: int, config: ChapterDetectionConfig):
    """智能检测书籍章节"""

@router.get("/books/{book_id}/chapters")
async def get_chapters(book_id: int):
    """获取书籍章节列表"""

@router.post("/books/{book_id}/chapters")
async def create_chapter(book_id: int, chapter: ChapterCreate):
    """手动创建章节"""

@router.put("/chapters/{chapter_id}")
async def update_chapter(chapter_id: int, chapter: ChapterUpdate):
    """更新章节信息"""

@router.post("/chapters/{chapter_id}/split")
async def split_chapter(chapter_id: int, split_point: int):
    """分割章节"""

@router.post("/chapters/merge")
async def merge_chapters(chapter_ids: List[int]):
    """合并章节"""
```

### 2. 智能分析API (`/api/analysis`)
```python
# 分析会话管理
@router.post("/projects/{project_id}/analysis/sessions")
async def create_analysis_session(project_id: int, config: AnalysisConfig):
    """创建分析会话"""

@router.post("/analysis/sessions/{session_id}/start")
async def start_analysis_session(session_id: int):
    """启动分析任务"""

@router.get("/analysis/sessions/{session_id}")
async def get_analysis_session(session_id: int):
    """获取会话状态"""

@router.post("/analysis/sessions/{session_id}/pause")
async def pause_analysis_session(session_id: int):
    """暂停分析任务"""

@router.post("/analysis/sessions/{session_id}/cancel")
async def cancel_analysis_session(session_id: int):
    """取消分析任务"""

@router.get("/analysis/sessions/{session_id}/results")
async def get_analysis_results(session_id: int):
    """获取分析结果"""

@router.put("/analysis/results/{result_id}")
async def update_analysis_result(result_id: int, config: UserConfig):
    """更新用户配置"""
```

### 3. 合成任务API (`/api/synthesis`)
```python
# 合成任务管理
@router.post("/projects/{project_id}/synthesis/tasks")
async def create_synthesis_task(project_id: int, config: SynthesisConfig):
    """创建合成任务"""

@router.post("/synthesis/tasks/{task_id}/start")
async def start_synthesis_task(task_id: int):
    """启动合成任务"""

@router.get("/synthesis/tasks/{task_id}")
async def get_synthesis_task(task_id: int):
    """获取任务状态"""

@router.post("/synthesis/tasks/{task_id}/pause")
async def pause_synthesis_task(task_id: int):
    """暂停合成任务"""

@router.get("/synthesis/tasks/{task_id}/files")
async def get_synthesis_files(task_id: int):
    """获取生成的音频文件"""

@router.post("/synthesis/tasks/{task_id}/merge")
async def merge_synthesis_files(task_id: int, config: MergeConfig):
    """合并音频文件"""
```

### 4. 配置预设API (`/api/presets`)
```python
# 配置预设管理
@router.get("/presets")
async def get_presets(scope: str = "global", scope_id: int = None):
    """获取预设列表"""

@router.post("/presets")
async def save_preset(preset: PresetCreate):
    """保存预设配置"""

@router.get("/presets/{preset_id}")
async def get_preset(preset_id: int):
    """获取特定预设"""

@router.put("/presets/{preset_id}")
async def update_preset(preset_id: int, preset: PresetUpdate):
    """更新预设"""

@router.delete("/presets/{preset_id}")
async def delete_preset(preset_id: int):
    """删除预设"""
```

## 🧩 **核心服务层设计**

### 1. ChapterService
```python
class ChapterService:
    def __init__(self, db: Session):
        self.db = db
        
    async def detect_chapters_auto(self, book_id: int, config: ChapterDetectionConfig):
        """自动检测章节"""
        book = self.db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(404, "书籍不存在")
            
        # 智能章节检测逻辑
        detector = ChapterDetector(config)
        chapters = detector.detect(book.content)
        
        # 保存章节到数据库
        for i, chapter_data in enumerate(chapters):
            chapter = BookChapter(
                book_id=book_id,
                chapter_number=i + 1,
                chapter_title=chapter_data['title'],
                content=chapter_data['content'],
                word_count=len(chapter_data['content'])
            )
            self.db.add(chapter)
            
        # 更新书籍状态
        book.structure_status = 'structured'
        book.total_chapters = len(chapters)
        self.db.commit()
        
        return chapters
        
    async def split_chapter(self, chapter_id: int, split_point: int):
        """分割章节"""
        chapter = self.db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(404, "章节不存在")
            
        # 分割逻辑
        content1 = chapter.content[:split_point]
        content2 = chapter.content[split_point:]
        
        # 更新原章节
        chapter.content = content1
        chapter.word_count = len(content1)
        
        # 创建新章节
        new_chapter = BookChapter(
            book_id=chapter.book_id,
            chapter_number=chapter.chapter_number + 0.5,  # 临时编号
            content=content2,
            word_count=len(content2)
        )
        self.db.add(new_chapter)
        
        # 重新排序章节编号
        await self._reorder_chapters(chapter.book_id)
        self.db.commit()
```

### 2. AnalysisService
```python
class AnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.llm_client = DifyClient()
        self.task_queue = AnalysisTaskQueue()
        
    async def create_session(self, project_id: int, config: AnalysisConfig):
        """创建分析会话"""
        # 验证项目
        project = self.db.query(NovelProject).filter(NovelProject.id == project_id).first()
        if not project:
            raise HTTPException(404, "项目不存在")
            
        # 获取目标内容
        targets = await self._get_analysis_targets(config.target_type, config.target_ids)
        
        # 创建会话
        session = AnalysisSession(
            project_id=project_id,
            book_id=project.book_id,
            target_type=config.target_type,
            target_ids=json.dumps(config.target_ids),
            llm_provider=config.llm_provider,
            llm_workflow_id=config.workflow_id,
            total_tasks=len(targets)
        )
        self.db.add(session)
        self.db.commit()
        
        return session
        
    async def start_session(self, session_id: int):
        """启动分析会话"""
        session = self.db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
        if not session:
            raise HTTPException(404, "会话不存在")
            
        # 更新状态
        session.status = 'running'
        session.started_at = datetime.utcnow()
        self.db.commit()
        
        # 启动后台任务
        await self.task_queue.enqueue_analysis_tasks(session)
        
        return {"success": True, "message": "分析任务已启动"}
        
    async def process_chapter_analysis(self, session_id: int, chapter_id: int):
        """处理单个章节的分析"""
        try:
            session = self.db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
            chapter = self.db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
            
            # 调用大模型
            llm_response = await self.llm_client.analyze_chapter(
                content=chapter.content,
                workflow_id=session.llm_workflow_id
            )
            
            # 解析结果
            parsed_result = self._parse_llm_response(llm_response)
            
            # 保存结果
            result = AnalysisResult(
                session_id=session_id,
                chapter_id=chapter_id,
                input_text=chapter.content,
                input_hash=hashlib.md5(chapter.content.encode()).hexdigest(),
                raw_response=llm_response,
                project_info=parsed_result['project_info'],
                synthesis_plan=parsed_result['synthesis_plan'],
                characters=parsed_result['characters'],
                llm_response_time=llm_response.get('response_time', 0)
            )
            self.db.add(result)
            
            # 更新章节状态
            chapter.analysis_status = 'completed'
            
            # 更新会话进度
            session.completed_tasks += 1
            session.progress = int((session.completed_tasks / session.total_tasks) * 100)
            
            if session.completed_tasks >= session.total_tasks:
                session.status = 'completed'
                session.completed_at = datetime.utcnow()
                
            self.db.commit()
            
            # 发送WebSocket进度更新
            await self._send_progress_update(session_id, session.progress, result)
            
        except Exception as e:
            # 错误处理
            session.failed_tasks += 1
            session.error_message = str(e)
            self.db.commit()
            
            await self._send_error_update(session_id, str(e))
```

### 3. SynthesisService
```python
class SynthesisService:
    def __init__(self, db: Session):
        self.db = db
        self.tts_client = MegaTTSClient()
        self.task_queue = SynthesisTaskQueue()
        
    async def create_task(self, project_id: int, config: SynthesisConfig):
        """创建合成任务"""
        # 获取分析结果
        analysis_result = self.db.query(AnalysisResult).filter(
            AnalysisResult.id == config.analysis_result_id
        ).first()
        
        if not analysis_result:
            raise HTTPException(404, "分析结果不存在")
            
        # 创建合成任务
        task = SynthesisTask(
            project_id=project_id,
            analysis_result_id=config.analysis_result_id,
            chapter_id=analysis_result.chapter_id,
            synthesis_plan=analysis_result.final_config or analysis_result.synthesis_plan,
            batch_size=config.batch_size,
            total_segments=len(analysis_result.synthesis_plan['segments'])
        )
        self.db.add(task)
        self.db.commit()
        
        return task
        
    async def start_task(self, task_id: int):
        """启动合成任务"""
        task = self.db.query(SynthesisTask).filter(SynthesisTask.id == task_id).first()
        if not task:
            raise HTTPException(404, "任务不存在")
            
        # 更新状态
        task.status = 'running'
        task.started_at = datetime.utcnow()
        self.db.commit()
        
        # 启动后台合成
        await self.task_queue.enqueue_synthesis_segments(task)
        
        return {"success": True, "message": "合成任务已启动"}
        
    async def process_segment_synthesis(self, task_id: int, segment_data: dict):
        """处理单个片段的合成"""
        try:
            task = self.db.query(SynthesisTask).filter(SynthesisTask.id == task_id).first()
            
            # 调用TTS API
            audio_result = await self.tts_client.synthesize(
                text=segment_data['text'],
                voice_id=segment_data['voice_id'],
                parameters=segment_data['parameters']
            )
            
            # 保存音频文件
            audio_file = AudioFile(
                filename=audio_result['filename'],
                file_path=audio_result['file_path'],
                project_id=task.project_id,
                text_content=segment_data['text'],
                voice_profile_id=segment_data['voice_id'],
                audio_type='segment',
                processing_time=audio_result['processing_time']
            )
            self.db.add(audio_file)
            
            # 更新任务进度
            task.completed_segments += 1
            task.progress = int((task.completed_segments / task.total_segments) * 100)
            
            # 更新输出文件列表
            output_files = json.loads(task.output_files or '[]')
            output_files.append({
                'segment_id': segment_data['segment_id'],
                'file_path': audio_result['file_path'],
                'audio_file_id': audio_file.id
            })
            task.output_files = json.dumps(output_files)
            
            if task.completed_segments >= task.total_segments:
                task.status = 'completed'
                task.completed_at = datetime.utcnow()
                
            self.db.commit()
            
            # 发送进度更新
            await self._send_synthesis_progress(task_id, task.progress)
            
        except Exception as e:
            # 错误处理和重试逻辑
            await self._handle_synthesis_error(task_id, segment_data, str(e))
```

### 4. PresetService
```python
class PresetService:
    def __init__(self, db: Session):
        self.db = db
        
    async def save_preset(self, preset_data: PresetCreate):
        """保存预设配置"""
        preset = UserPreset(
            name=preset_data.name,
            description=preset_data.description,
            config_type=preset_data.config_type,
            config_data=preset_data.config_data,
            scope=preset_data.scope,
            scope_id=preset_data.scope_id
        )
        self.db.add(preset)
        self.db.commit()
        return preset
        
    async def get_presets(self, scope: str = "global", scope_id: int = None):
        """获取预设列表"""
        query = self.db.query(UserPreset).filter(UserPreset.scope == scope)
        if scope_id:
            query = query.filter(UserPreset.scope_id == scope_id)
            
        return query.order_by(UserPreset.usage_count.desc()).all()
        
    async def apply_preset(self, preset_id: int):
        """应用预设配置"""
        preset = self.db.query(UserPreset).filter(UserPreset.id == preset_id).first()
        if not preset:
            raise HTTPException(404, "预设不存在")
            
        # 更新使用统计
        preset.usage_count += 1
        preset.last_used = datetime.utcnow()
        self.db.commit()
        
        return preset.config_data
```

## 🔄 **WebSocket实时通信**

### 进度推送服务
```python
class ProgressWebSocketManager:
    def __init__(self):
        self.connections = {}
        
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.connections:
            self.connections[session_id] = []
        self.connections[session_id].append(websocket)
        
    async def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.connections:
            self.connections[session_id].remove(websocket)
            
    async def send_progress_update(self, session_id: str, data: dict):
        if session_id in self.connections:
            for connection in self.connections[session_id]:
                try:
                    await connection.send_json({
                        "type": "progress",
                        "data": data
                    })
                except:
                    # 移除断开的连接
                    self.connections[session_id].remove(connection)
                    
    async def send_result_update(self, session_id: str, result: dict):
        if session_id in self.connections:
            for connection in self.connections[session_id]:
                try:
                    await connection.send_json({
                        "type": "result",
                        "data": result
                    })
                except:
                    self.connections[session_id].remove(connection)

# WebSocket路由
@app.websocket("/ws/analysis/{session_id}")
async def analysis_websocket(websocket: WebSocket, session_id: str):
    await progress_manager.connect(websocket, f"analysis_{session_id}")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await progress_manager.disconnect(websocket, f"analysis_{session_id}")

@app.websocket("/ws/synthesis/{task_id}")
async def synthesis_websocket(websocket: WebSocket, task_id: str):
    await progress_manager.connect(websocket, f"synthesis_{task_id}")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await progress_manager.disconnect(websocket, f"synthesis_{task_id}")
```

## 🎯 **关键技术要点**

### 1. 大模型集成
- **异步调用** - 避免阻塞
- **错误重试** - 网络异常处理
- **结果缓存** - 避免重复分析
- **速率限制** - 控制并发请求

### 2. 任务队列
- **Redis队列** - 可靠的任务调度
- **优先级处理** - 重要任务优先
- **失败重试** - 自动重试机制
- **进度跟踪** - 实时状态更新

### 3. 文件管理
- **批量处理** - 提高效率
- **增量备份** - 数据安全
- **清理策略** - 磁盘空间管理
- **访问控制** - 权限管理

### 4. 性能优化
- **数据库索引** - 查询优化
- **连接池** - 资源管理
- **缓存策略** - 减少重复计算
- **异步处理** - 提高并发 