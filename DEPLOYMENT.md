# Expense Tracking K8s 部署文档

## 环境说明

- Kubernetes: Docker Desktop 内置 K8s
- 镜像: 本地构建，无需推送到远程仓库
- Ingress Controller: ingress-nginx（复用已有集群）

---

## 部署步骤

### 1. 编写 Dockerfile

在项目根目录（和 `manage.py` 同级）新建 `Dockerfile`，无后缀。

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

**各行说明：**
- `FROM python:3.11-slim` — 官方 Python 精简镜像，体积小
- `WORKDIR /app` — 容器内工作目录
- `COPY requirements.txt .` — 先单独复制依赖文件，利用 Docker 层缓存
- `RUN pip install --no-cache-dir -r requirements.txt` — 安装依赖，`--no-cache-dir` 减少镜像体积
- `COPY . .` — 复制项目所有文件，放在安装依赖之后利用缓存
- `EXPOSE 8000` — 声明容器监听端口（文档性，不真正开放）
- `CMD` — 容器启动命令，`0.0.0.0` 表示监听所有网络接口

---

### 2. 构建镜像

```bash
cd /Users/alex/demo/devops/expense-tracking-main
docker build -t expense-tracking:v1 .
```

- `-t expense-tracking:v1` — 镜像名称和版本号
- `.` — 使用当前目录的 Dockerfile

Docker Desktop K8s 直接使用本地镜像，无需额外导入。

---

### 3. 创建 Namespace

```bash
kubectl create namespace k8s-expense
```

Namespace 是 K8s 的逻辑隔离空间，不同项目放在不同 namespace 互不干扰。

---

### 4. 编写 K8s Manifests

在项目根目录下新建 `k8s/` 目录，存放所有 K8s 配置文件。

#### 4.1 deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: expense-deployment
  namespace: k8s-expense
  labels:
    app: expense
spec:
  replicas: 1
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: expense
  template:
    metadata:
      labels:
        app: expense
    spec:
      containers:
        - name: expense
          image: expense-tracking:v1
          imagePullPolicy: Never
          ports:
            - containerPort: 8000
          env:
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: expense-secret
                  key: SECRET_KEY
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
          livenessProbe:
            httpGet:
              path: /
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 20
          readinessProbe:
            httpGet:
              path: /
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
```

**关键字段说明：**
- `replicas` — Pod 副本数
- `strategy.rollingUpdate` — 滚动更新策略，`maxSurge: 1` 允许多出 1 个新 Pod，`maxUnavailable: 0` 保证更新期间服务不中断
- `selector.matchLabels` — Deployment 通过标签找到它管理的 Pod，必须和 template.labels 一致
- `imagePullPolicy: Never` — 使用本地镜像，不去远程拉取
- `containerPort` — 和 Dockerfile EXPOSE 端口一致
- `resources.requests` — Pod 启动时申请的最低资源，K8s 用于调度决策
- `resources.limits` — Pod 能用的最大资源，超出 CPU 被限速，超出内存被 OOMKill
- `livenessProbe` — 检查容器是否存活，失败则重启；等 15 秒后每 20 秒检查一次
- `readinessProbe` — 检查容器是否就绪，失败则从 Service 摘掉不重启；等 5 秒后每 10 秒检查一次

#### 4.2 service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: expense-service
  namespace: k8s-expense
  labels:
    app: expense
spec:
  selector:
    app: expense
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP
```

**关键字段说明：**
- `selector` — 通过标签找到 Pod，必须和 Deployment labels 一致
- `port: 80` — Service 对外暴露的端口
- `targetPort: 8000` — 转发到 Pod 的端口，和 containerPort 一致
- `type: ClusterIP` — 仅集群内部访问，对外靠 Ingress

#### 4.3 ingress.yaml

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: expense-ingress
  namespace: k8s-expense
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - host: expense.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: expense-service
                port:
                  number: 80
```

**关键字段说明：**
- `annotations` — 给 ingress-nginx 的额外配置
- `ingressClassName: nginx` — 指定使用 nginx ingress controller
- `host: expense.local` — 访问域名，需在 `/etc/hosts` 配置
- `backend.service.name` — 对应 service.yaml 的 name
- `port.number` — 对应 Service 的 port

---

### 5. 创建 K8s Secret

敏感信息（如 Django 的 `SECRET_KEY`）不能写在 yaml 文件里，否则提交 git 后会永久暴露。使用 K8s Secret 存储在集群中。

```bash
# 生成随机 SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# 创建 Secret
kubectl create secret generic expense-secret \
  --from-literal=SECRET_KEY='<生成的值>' \
  -n k8s-expense
```

在 `deployment.yaml` 的 `containers` 下引用 Secret：

```yaml
          env:
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: expense-secret
                  key: SECRET_KEY
```

**说明：**
- Secret 以 Base64 编码存储在集群里，不进代码库
- 生产环境更严格的方案是 Vault 或云厂商 KMS

---

### 6. 部署到集群

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

---

### 7. 验证部署状态

```bash
# 查看 Pod 状态
kubectl get pods -n k8s-expense

# 查看 Pod 日志（排查问题）
kubectl logs -n k8s-expense <pod-name>

# 查看所有资源
kubectl get all -n k8s-expense
```

**常见 Pod 状态：**
- `Running` — 正常运行
- `CrashLoopBackOff` — 容器反复崩溃，查看日志排查原因
- `Pending` — 等待调度，可能是资源不足

---

## 架构说明

```
用户请求
   ↓
Ingress (expense.local)
   ↓
Service (ClusterIP, port 80)
   ↓
Pod (Django, port 8000)
```

不使用 LoadBalancer，单体应用用 Ingress + ClusterIP Service 即可。

---

## 注意事项

- yaml 缩进必须用空格，不能用 Tab
- `selector` 标签必须和 `labels` 完全一致，否则 Service 找不到 Pod
- `imagePullPolicy: Never` 使用本地镜像时必须加，否则 K8s 会尝试从远程拉取
- 敏感信息（如 `SECRET_KEY`）不能直接写在 yaml 里，应使用 K8s Secret

---

### 8. 配置本地 DNS 解析

`expense.local` 是假域名，需要在本机 `/etc/hosts` 里手动映射，让浏览器能找到它。

```bash
sudo sh -c 'echo "127.0.0.1 expense.local" >> /etc/hosts'
```

**说明：**
- 系统查 DNS 之前会先读 `/etc/hosts`，找到映射直接用，不走 DNS 服务器
- 只在本机有效，其他人无法通过 `expense.local` 访问

访问 `http://expense.local` 验证部署成功。

---

## Troubleshooting

### 查看资源状态

```bash
# 查看所有资源
kubectl get all -n k8s-expense

# 查看 Pod 状态
kubectl get pods -n k8s-expense

# 查看 Pod 详细信息（排查 Pending、CrashLoopBackOff）
kubectl describe pod <pod-name> -n k8s-expense

# 查看 Pod 日志
kubectl logs -n k8s-expense <pod-name>

# 查看前一个崩溃容器的日志
kubectl logs -n k8s-expense <pod-name> --previous
```

### 常见问题

| 状态 | 原因 | 排查方法 |
|------|------|---------|
| `CrashLoopBackOff` | 容器启动后崩溃 | `kubectl logs` 看报错 |
| `Pending` | 无法调度到节点 | `kubectl describe pod` 看 Events |
| `ImagePullBackOff` | 镜像拉取失败 | 检查镜像名、`imagePullPolicy` |
| `OOMKilled` | 内存超出 limits | 调高 `resources.limits.memory` |
| 服务无法访问 | Service/Ingress 配置问题 | 检查 selector 标签是否一致 |

### 查看资源使用情况

```bash
# 查看 Pod 实际 CPU/内存消耗（用于调整 resources）
kubectl top pod -n k8s-expense
```

### 进入容器调试

```bash
kubectl exec -it <pod-name> -n k8s-expense -- /bin/bash
```

### 重新部署

```bash
# 强制重启 Pod（不改配置）
kubectl rollout restart deployment/expense-deployment -n k8s-expense

# 查看滚动更新状态
kubectl rollout status deployment/expense-deployment -n k8s-expense

# 查看历史版本
kubectl rollout history deployment/expense-deployment -n k8s-expense

# 回滚到上一个版本
kubectl rollout undo deployment/expense-deployment -n k8s-expense

# 回滚到指定版本
kubectl rollout undo deployment/expense-deployment -n k8s-expense --to-revision=<版本号>
```

### 常见排查流程

根据状态名决定用哪个命令：

| 状态 | 先看什么 |
|------|---------|
| `CreateContainerConfigError` | 直接 `describe`，看 Events |
| `CrashLoopBackOff` | 先 `logs --previous`，再 `describe` |
| `Pending` | 直接 `describe`，看 Events |
| `OOMKilled` | `describe` 看 Last State |
| `503` | `kubectl describe ingress` 看 Backends |

**CrashLoopBackOff / BackOff：**
1. `kubectl logs <pod> -n k8s-expense --previous` — 看上次崩溃日志
2. `kubectl describe pod <pod> -n k8s-expense` — 看 Last State 的 Reason 和 Exit Code

**Exit Code 含义：**
- `Exit Code: 1` — 应用自身报错（如缺少环境变量）
- `Exit Code: 137` — OOMKilled，内存超出 limits

**OOM 特征：**
- 日志为空（来不及输出就被杀）
- `Last State: Reason: OOMKilled`
- `Exit Code: 137`

**Ingress 503：**
- 请求到了 ingress-nginx，但后端 Service 找不到或不可用
- `kubectl describe ingress` 看 Rules 里的 Backends 是否有 error

### Troubleshooting 场景记录

| 场景 | 状态 | 关键命令 | 根本原因 |
|------|------|---------|---------|
| 错误镜像名 | `ErrImageNeverPull` | 看状态名即可 | 本地无此镜像，imagePullPolicy: Never 阻止拉取 |
| 内存不足 | `CrashLoopBackOff` | `describe` 看 Exit Code 137 | memory limits 太低，OOMKilled |
| Secret 丢失 | `CreateContainerConfigError` | `describe` 看 Events | 集群里找不到 Secret |
| Ingress 配置错误 | 浏览器 503 | `describe ingress` 看 Backends | Service 名字错误 |

### 注意事项

- `kubectl set` 只改集群状态，不更新本地文件，会导致集群和文件不一致
- 永久性变更应该改本地 yaml 文件再 `kubectl apply`
- `kubectl set` 只用于临时调试
- 出问题时 `kubectl apply -f` 本地文件是最可靠的恢复方式
- `rollout undo` 回滚前先用 `rollout history` 确认目标版本有完整配置，否则可能回到缺少环境变量的旧版本

---

## 待完善

- [x] 配置 K8s Secret 管理敏感环境变量
- [x] 配置 `/etc/hosts` 访问 expense.local
- [x] 添加 livenessProbe / readinessProbe 健康检查
- [x] 配置资源限制（resources requests/limits）
- [x] 配置滚动更新策略（RollingUpdate）
- [x] 配置 HPA 自动扩缩容（minReplicas: 1，maxReplicas: 3，CPU 70%）
- [x] 配置 ConfigMap 管理非敏感配置（DEBUG、ALLOWED_HOSTS、DJANGO_SETTINGS_MODULE）
- [x] 配置 PVC 持久化存储 SQLite 数据（mountPath: /app/db）
- [ ] 安装 metrics-server（HPA 需要获取真实 CPU 数据）
- [ ] 生产环境替换 SQLite 为 PostgreSQL
- [ ] 替换 Django runserver 为 gunicorn
