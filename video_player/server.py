#!/usr/bin/env python3
"""
简单的视频服务器
用于提供视频列表和视频文件流式传输
"""

import os
import json
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
import mimetypes

# 配置
SEARCH_DIR = "."  # 搜索目录 (当前目录)
PORT = 8000
EXCLUDE_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env'}  # 排除的目录

class VideoServerHandler(SimpleHTTPRequestHandler):
    """自定义请求处理器"""
    
    def do_GET(self):
        """处理 GET 请求"""
        
        # 处理 API 请求: 获取视频列表
        if self.path == '/api/videos':
            self.send_video_list()
            return
        
        # 处理视频文件请求
        if self.path.startswith('/videos/'):
            self.serve_video_file()
            return
        
        # 处理其他文件请求 (HTML, CSS, JS等)
        super().do_GET()
    
    def send_video_list(self):
        """发送视频列表 JSON - 递归搜索所有 MP4 文件"""
        try:
            search_path = Path(SEARCH_DIR).resolve()
            
            # 递归扫描 mp4 文件
            video_files = []
            
            def scan_directory(directory):
                """递归扫描目录"""
                try:
                    for item in directory.iterdir():
                        # 跳过隐藏文件和排除的目录
                        if item.name.startswith('.') or item.name in EXCLUDE_DIRS:
                            continue
                        
                        if item.is_file() and item.suffix.lower() == '.mp4':
                            # 计算相对路径
                            relative_path = item.relative_to(search_path)
                            # 获取文件大小(以 MB 为单位)
                            size_mb = item.stat().st_size / (1024 * 1024)
                            
                            video_files.append({
                                'name': item.name,
                                'path': f'/videos/{relative_path.as_posix()}',
                                'relative_path': str(relative_path),
                                'size': item.stat().st_size,
                                'size_mb': round(size_mb, 2),
                                'directory': str(relative_path.parent) if relative_path.parent != Path('.') else '根目录'
                            })
                        
                        elif item.is_dir():
                            # 递归扫描子目录
                            scan_directory(item)
                
                except PermissionError:
                    # 跳过没有权限的目录
                    pass
            
            # 开始扫描
            scan_directory(search_path)
            
            # 按路径排序
            video_files.sort(key=lambda x: x['relative_path'])
            
            # 发送 JSON 响应
            response = json.dumps(video_files, ensure_ascii=False, indent=2)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', len(response.encode()))
            self.end_headers()
            self.wfile.write(response.encode())
            
            print(f"已发送视频列表: {len(video_files)} 个文件")
            
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
            self.send_error(500, f"服务器错误: {str(e)}")
    
    def serve_video_file(self):
        """提供视频文件流式传输"""
        try:
            # 解码 URL 并获取文件路径
            # 路径格式: /videos/relative/path/to/file.mp4
            url_path = unquote(self.path)
            if url_path.startswith('/videos/'):
                relative_path = url_path[8:]  # 去掉 '/videos/'
                full_path = Path(SEARCH_DIR).resolve() / relative_path
            else:
                self.send_error(400, "无效的请求路径")
                return
            
            if not full_path.exists() or not full_path.is_file():
                self.send_error(404, "文件不存在")
                return
            
            # 获取文件大小
            file_size = full_path.stat().st_size
            
            # 检查是否是 Range 请求(用于视频拖动)
            range_header = self.headers.get('Range')
            
            if range_header:
                # 解析 Range 请求
                byte_range = range_header.replace('bytes=', '').split('-')
                start = int(byte_range[0])
                end = int(byte_range[1]) if byte_range[1] else file_size - 1
                
                # 发送部分内容响应
                self.send_response(206)
                self.send_header('Content-Type', 'video/mp4')
                self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                self.send_header('Content-Length', end - start + 1)
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()
                
                # 读取并发送指定范围的数据
                with open(full_path, 'rb') as f:
                    f.seek(start)
                    chunk_size = 1024 * 1024  # 1MB chunks
                    remaining = end - start + 1
                    while remaining > 0:
                        chunk = f.read(min(chunk_size, remaining))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)
            else:
                # 发送完整文件
                self.send_response(200)
                self.send_header('Content-Type', 'video/mp4')
                self.send_header('Content-Length', file_size)
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()
                
                with open(full_path, 'rb') as f:
                    chunk_size = 1024 * 1024  # 1MB chunks
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
            
            print(f"已提供视频: {full_path.name}")
            
        except Exception as e:
            print(f"错误: {e}")
            self.send_error(500, f"服务器错误: {str(e)}")
    
    def log_message(self, format, *args):
        """自定义日志输出"""
        print(f"[{self.log_date_time_string()}] {format % args}")


def main():
    """启动服务器"""
    
    # 扫描并显示视频文件统计
    search_path = Path(SEARCH_DIR).resolve()
    print("=" * 60)
    print(f"🎬 视频服务器已启动!")
    print(f"📁 搜索目录: {search_path}")
    print(f"🔍 正在递归搜索 MP4 文件...")
    
    # 快速统计视频数量
    video_count = len(list(search_path.rglob('*.mp4')))
    print(f"📊 找到 {video_count} 个 MP4 视频文件")
    
    # 创建服务器
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, VideoServerHandler)
    
    print(f"🌐 访问地址: http://localhost:{PORT}")
    print(f"🔗 直接打开: http://localhost:{PORT}/index.html")
    print("=" * 60)
    print("按 Ctrl+C 停止服务器")
    print()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 服务器已停止")
        httpd.shutdown()


if __name__ == '__main__':
    main()
