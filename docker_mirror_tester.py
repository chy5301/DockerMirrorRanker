import concurrent.futures
import re
import threading
import time

import requests
import urllib3

# 禁用SSL证书警告，因为某些镜像可能使用自签名证书
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 创建线程锁，用于同步控制台输出，避免多线程打印混乱
print_lock = threading.Lock()


def load_mirrors_from_md(file_path):
    """
    从Markdown文件读取有效镜像列表
    格式要求：第一列为`包裹的镜像地址，第二列为状态（支持：正常/新增）
    """
    valid_status = {"正常", "新增"}
    pattern = r"`([\w\.\-]+)`.*?\|.*?(\S+)\s*\|"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # 跳过表头前两行（标题和分隔符）
            for _ in range(2):
                next(f)

            # 使用列表推导式过滤出有效的镜像地址
            return [
                match.group(1)  # 提取镜像地址
                for line in f
                if (match := re.search(pattern, line))  # 使用海象运算符进行模式匹配
                and match.group(2) in valid_status  # 确保状态有效
            ]
    except Exception as e:
        print(f"\033[31mError reading markdown file: {str(e)}\033[0m")
        return []


def test_mirror(mirror):
    global start_time
    url = f"https://{mirror}"
    success = 0  # 成功请求计数
    total_time = 0.0  # 总响应时间
    attempts = 5  # 每个镜像测试次数
    log_buffer = []  # 日志缓存器，用于收集所有测试过程的日志

    # 初始化日志，使用ANSI转义序列添加颜色和样式
    log_buffer.append(f"\n\033[1m▶ Testing {url}\033[0m")

    for i in range(attempts):
        attempt_log = ""
        try:
            start_time = time.time()
            # 发送HEAD请求到镜像的v2接口，设置5秒超时并禁用SSL验证
            response = requests.head(f"{url}/v2/", timeout=5, verify=False)
            elapsed = time.time() - start_time

            # 检查响应状态码，200和401都视为成功（401表示需要认证，但服务是正常的）
            if response.status_code in (200, 401):
                success += 1
                total_time += elapsed
                status_desc = (
                    f"\033[32m{response.status_code} OK\033[0m"  # 绿色显示成功
                )
            else:
                status_desc = (
                    f"\033[33m{response.status_code} Error\033[0m"  # 黄色显示错误
                )

            attempt_log = f"  Attempt {i + 1}: {status_desc} ({elapsed:.2f}s)"

        except Exception as e:
            elapsed = time.time() - start_time if "start_time" in locals() else 0
            error_msg = str(e).split(":")[0]  # 提取错误信息的主要部分
            attempt_log = f"  Attempt {i + 1}: \033[31mFailed ({error_msg})\033[0m"  # 红色显示失败

        finally:
            log_buffer.append(attempt_log)
            time.sleep(1)  # 请求间隔1秒，避免过于频繁

    # 计算统计指标：成功率和平均响应时间
    success_rate = success / attempts
    avg_time = total_time / success if success > 0 else float("inf")

    # 根据成功率选择状态图标和颜色
    status_icon = "\033[32m✓\033[0m" if success_rate > 0.5 else "\033[31m✗\033[0m"
    log_buffer.append(
        f"{status_icon} 最终结果: "
        f"成功率 {success_rate * 100:.1f}% | "
        f"平均响应 {avg_time:.2f}s"
    )

    # 使用线程锁确保日志输出的原子性
    with print_lock:
        print("\n".join(log_buffer))

    return {"url": url, "success_rate": success_rate, "avg_time": avg_time}


if __name__ == "__main__":
    # 从当前目录读取 mirrors.md 文件
    MIRROR_FILE = "mirrors.md"
    mirror_list = load_mirrors_from_md(MIRROR_FILE)

    if not mirror_list:
        print("\033[31m未找到有效镜像地址，请检查markdown文件格式！\033[0m")
        exit(1)

    print(f"\033[1m成功加载 {len(mirror_list)} 个有效镜像\033[0m")

    print("\033[1m\n开始测试镜像加速器...\033[0m")
    start_time = time.time()

    # 使用线程池并发测试所有镜像，最大并发数为10
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # 提交所有测试任务到线程池
        futures = {
            executor.submit(test_mirror, mirror): mirror for mirror in mirror_list
        }

        # 收集测试结果
        for future in concurrent.futures.as_completed(futures):
            data = future.result()
            results.append(data)
            # 使用线程锁同步输出结果
            with print_lock:
                status_color = (
                    "\033[32m✓\033[0m"
                    if data["success_rate"] > 0.5
                    else "\033[31m✗\033[0m"
                )
                print(
                    f"{status_color} {data['url']}: "
                    f"成功率 {data['success_rate'] * 100:.1f}% | "
                    f"平均响应 {data['avg_time']:.2f}s"
                )

    # 根据成功率和响应时间对结果进行排序（成功率优先，响应时间次之）
    sorted_results = sorted(results, key=lambda x: (-x["success_rate"], x["avg_time"]))

    # 输出排序后的结果，使用不同颜色表示不同成功率
    print("\n\033[1m测试结果排序（最佳到最差）：\033[0m")
    for idx, res in enumerate(sorted_results, 1):
        color_code = (
            "\033[32m"
            if res["success_rate"] > 0.7
            else "\033[33m"
            if res["success_rate"] > 0.3
            else "\033[31m"
        )
        print(
            f"{idx:2d}. {color_code}{res['url']}\033[0m "
            f"(成功率: {res['success_rate'] * 100:.1f}%, "
            f"响应: {res['avg_time']:.2f}s)"
        )

    print(f"\n总测试时间: {time.time() - start_time:.1f}秒")

    # 过滤出可用的镜像（成功率大于0）并保存到文件
    print("\n\033[1m可用镜像列表（过滤零成功率镜像）：\033[0m")
    valid_mirrors = [res["url"] for res in sorted_results if res["success_rate"] > 0]

    # 在控制台输出可用镜像列表
    for idx, url in enumerate(valid_mirrors, 1):
        print(f"{idx:2d}. \033[34m{url}\033[0m")

    # 将可用镜像列表保存到文件
    with open("valid_mirrors.txt", "w") as f:
        f.write("\n".join(valid_mirrors))

    print(
        f"\n\033[36m生成可用镜像列表：{len(valid_mirrors)} 条 → valid_mirrors.txt\033[0m"
    )
