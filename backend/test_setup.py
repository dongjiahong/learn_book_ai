#!/usr/bin/env python3
"""
测试项目初始化是否成功
"""
import os
from pathlib import Path

def test_project_structure():
    """测试项目目录结构"""
    required_dirs = [
        "app",
        "app/core",
        "app/api", 
        "app/models",
        "app/services",
        "tests"
    ]
    
    required_files = [
        "main.py",
        "requirements.txt",
        "config.toml",
        "app/__init__.py",
        "app/core/__init__.py",
        "app/core/config.py",
        "app/api/__init__.py",
        "app/models/__init__.py",
        "app/services/__init__.py",
        "tests/__init__.py"
    ]
    
    print("检查目录结构...")
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✓ {dir_path}")
        else:
            print(f"✗ {dir_path} - 缺失")
    
    print("\n检查文件...")
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - 缺失")
    
    print("\n检查配置文件内容...")
    if os.path.exists("config.toml"):
        with open("config.toml", 'r') as f:
            content = f.read()
            if "[database]" in content and "[llm]" in content:
                print("✓ config.toml 包含必要配置节")
            else:
                print("✗ config.toml 配置不完整")

if __name__ == "__main__":
    test_project_structure()
    print("\n项目初始化测试完成！")