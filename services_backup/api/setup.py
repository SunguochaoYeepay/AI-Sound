"""
AI-Sound API服务安装配置
"""

from setuptools import setup, find_packages

setup(
    name="ai-sound-api",
    version="1.0.0",
    description="AI-Sound TTS API Service",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "motor>=3.3.0",
        "httpx>=0.25.0",
        "websockets>=12.0",
        "python-multipart>=0.0.6",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
        ]
    }
)