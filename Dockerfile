FROM python:3.11-slim
# 指定基础镜像。python:3.11-slim 是官方 Python 镜像的精简版，体积小。
WORKDIR /app
# 在容器内创建并切换到 /app 目录，后续所有操作都在这里进行
COPY requirements.txt .
# 将当前目录下的 requirements.txt 文件复制到容器的 /app 目录中
RUN pip install --no-cache-dir -r requirements.txt
# 使用 pip 安装 requirements.txt 中列出的所有依赖项。--no-cache-dir 选项可以避免缓存安装包，减少镜像体积。
COPY . .
# 把项目所有文件复制进容器。放在安装依赖之后，就是为了利用上面说的缓存
EXPOSE 8000
# 声明容器在运行时会监听 8000 端口（Django 默认端口)
CMD ["python","manage.py","runserver","0.0.0.0:8000"]