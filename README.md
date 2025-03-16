# DockerMirrorRanker - Docker镜像源测速排名工具

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.6%2B-blue)

## 项目简介

DockerMirrorRanker 是一个用于测试和排名 Docker 镜像源速度和可用性的工具。在国内使用 Docker 时，由于网络原因，官方的 Docker Hub 往往速度较慢。本工具可以帮助您从众多镜像源中筛选出最快、最稳定的镜像源，提升 Docker 镜像拉取速度。

### 主要功能

- 自动测试多个 Docker 镜像源的连通性和响应速度
- 并发测试提高效率，快速得出结果
- 按照成功率和响应时间排序，筛选出最佳镜像源
- 生成可直接使用的镜像源列表

## 使用方法

### 前置条件

- Python 3.6 或更高版本
- 安装所需依赖：`requests`

```bash
pip install requests
```

### 步骤一：获取镜像源列表

1. 访问 [CodeJia 博客](https://www.coderjia.cn/archives/dba3f94c-a021-468a-8ac6-e840f85867ea) 获取最新的 Docker 镜像源列表
2. 将镜像源列表保存为 `mirrors.md` 文件，确保格式如下：

```markdown
| DockerHub 镜像仓库              | 是否正常 |
|-----------------------------|------|
| `mirror1.example.com`       | 正常   |
| `mirror2.example.com`       | 正常   |
| `mirror3.example.com`       | 新增   |
| `mirror4.example.com`       | 失效   |
```

> 注意：脚本只会测试标记为"正常"或"新增"的镜像源

### 步骤二：运行测试脚本

```bash
python docker_mirror_tester.py
```

### 步骤三：查看结果

脚本运行完成后，会在控制台显示测试结果，并生成 `valid_mirrors.txt` 文件，包含所有可用的镜像源地址。

测试结果示例：
```
成功加载 16 个有效镜像

开始测试镜像加速器...

▶ Testing https://mirror1.example.com
  Attempt 1: 200 OK (0.32s)
  Attempt 2: 200 OK (0.28s)
  ...
✓ 最终结果: 成功率 100.0% | 平均响应 0.30s

...

测试结果排序（最佳到最差）：
 1. https://best-mirror.example.com (成功率: 100.0%, 响应: 0.25s)
 2. https://good-mirror.example.com (成功率: 100.0%, 响应: 0.30s)
 ...

总测试时间: 15.3秒

可用镜像列表（过滤零成功率镜像）：
 1. https://best-mirror.example.com
 2. https://good-mirror.example.com
 ...

生成可用镜像列表：10 条 → valid_mirrors.txt
```

### 步骤四：使用测试结果

您可以将 `valid_mirrors.txt` 中的镜像源地址配置到 Docker 的 daemon.json 文件中：

```json
{
  "registry-mirrors": [
    "https://best-mirror.example.com",
    "https://good-mirror.example.com"
  ]
}
```

## 工作原理

1. 从 `mirrors.md` 文件中读取标记为"正常"或"新增"的镜像源地址
2. 对每个镜像源进行 5 次连接测试，记录成功率和平均响应时间
3. 根据成功率和响应时间对镜像源进行排序
4. 生成可用镜像源列表，保存到 `valid_mirrors.txt` 文件

## 致谢

- 感谢 [CodeJia 博客](https://www.coderjia.cn) 提供的镜像源列表
