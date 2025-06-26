# SongGeneration音乐生成服务Docker镜像
FROM juhayna/song-generation-levo:hf0613

# 设置工作目录
WORKDIR /workspace/SongGeneration

# 复制代码文件（不复制模型文件，使用volume挂载）
COPY MegaTTS/SongGeneration/*.py /workspace/SongGeneration/
COPY MegaTTS/SongGeneration/conf/ /workspace/SongGeneration/conf/
COPY MegaTTS/SongGeneration/codeclm/ /workspace/SongGeneration/codeclm/
COPY MegaTTS/SongGeneration/tools/ /workspace/SongGeneration/tools/
COPY MegaTTS/SongGeneration/libs/ /workspace/SongGeneration/libs/
COPY MegaTTS/SongGeneration/requirements*.txt /workspace/SongGeneration/

# 复制官方Gradio界面工具（如果存在）
COPY SongGeneration-Official-Demo/SongGeneration/tools/ /workspace/SongGeneration/tools/

# 模型文件通过volume挂载，不在镜像中复制

# 复制entrypoint脚本和Gradio包装脚本
COPY docker/songgeneration/docker-entrypoint.sh /workspace/SongGeneration/
COPY docker/songgeneration/gradio_wrapper.py /workspace/SongGeneration/

# 确保代码文件权限正确
RUN chmod -R 755 /workspace/SongGeneration
RUN chmod +x /workspace/SongGeneration/docker-entrypoint.sh
RUN chmod +x /workspace/SongGeneration/gradio_wrapper.py

# 安装额外依赖
RUN pip install --no-cache-dir requests pyyaml

# 创建必要的目录
RUN mkdir -p /workspace/SongGeneration/output /workspace/SongGeneration/temp

# 暴露端口 (API + Web界面)
EXPOSE 7862 7863 8081

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7863/health || exit 1

# 使用我们的entrypoint脚本
ENTRYPOINT ["/workspace/SongGeneration/docker-entrypoint.sh"] 