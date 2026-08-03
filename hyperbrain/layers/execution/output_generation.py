"""
输出生成模块 (Output Generation)

负责生成和管理各类输出内容。

功能：
- 生成文本输出
- 生成代码输出
- 生成Markdown格式
- 输出版本控制
- 输出质量检查
"""

import re
import uuid
import difflib
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from pydantic import BaseModel, Field, ConfigDict

from hyperbrain.core.logger import get_logger
from hyperbrain.core.config import get_config

logger = get_logger("execution.output")


class OutputType(str, Enum):
    """输出类型"""
    TEXT = "text"
    CODE = "code"
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"
    YAML = "yaml"
    TABLE = "table"
    LIST = "list"


class OutputFormat(str, Enum):
    """输出格式"""
    PLAIN = "plain"
    FORMATTED = "formatted"
    STRUCTURED = "structured"
    RICH = "rich"


class CodeLanguage(str, Enum):
    """代码语言"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"
    GO = "go"
    RUST = "rust"
    SQL = "sql"
    BASH = "bash"
    POWERSHELL = "powershell"
    HTML = "html"
    CSS = "css"
    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"
    TEXT = "text"


class OutputVersion(BaseModel):
    """输出版本"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    version_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)
    change_description: str = ""
    diff_from_previous: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_id": self.version_id,
            "timestamp": self.timestamp.isoformat(),
            "change_description": self.change_description,
            "content_preview": self.content[:100] + "..." if len(self.content) > 100 else self.content
        }


class GeneratedOutput(BaseModel):
    """生成的输出"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    output_type: OutputType = OutputType.TEXT
    format: OutputFormat = OutputFormat.PLAIN
    content: str = ""
    
    # 代码特定
    code_language: Optional[CodeLanguage] = None
    code_title: Optional[str] = None
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # 质量
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    quality_issues: List[str] = Field(default_factory=list)
    
    # 版本
    versions: List[OutputVersion] = Field(default_factory=list)
    current_version_index: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "output_type": self.output_type.value,
            "format": self.format.value,
            "content_length": len(self.content),
            "code_language": self.code_language.value if self.code_language else None,
            "quality_score": self.quality_score,
            "timestamp": self.timestamp.isoformat(),
            "version_count": len(self.versions)
        }
    
    def get_current_version(self) -> Optional[OutputVersion]:
        """获取当前版本"""
        if 0 <= self.current_version_index < len(self.versions):
            return self.versions[self.current_version_index]
        return None
    
    def get_version_history(self) -> List[Dict[str, Any]]:
        """获取版本历史"""
        return [v.to_dict() for v in self.versions]


class QualityCheckResult(BaseModel):
    """质量检查结果"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    checks_passed: List[str] = Field(default_factory=list)


class TextGenerator:
    """文本生成器"""
    
    def __init__(self):
        logger.info("TextGenerator initialized")
    
    def generate(self,
                 content: str,
                 format_type: OutputFormat = OutputFormat.PLAIN,
                 metadata: Optional[Dict[str, Any]] = None) -> GeneratedOutput:
        """
        生成文本输出
        
        Args:
            content: 内容
            format_type: 格式类型
            metadata: 元数据
            
        Returns:
            GeneratedOutput: 生成的输出
        """
        output = GeneratedOutput(
            output_type=OutputType.TEXT,
            format=format_type,
            content=content,
            metadata=metadata or {}
        )
        
        # 创建初始版本
        version = OutputVersion(
            content=content,
            change_description="Initial generation"
        )
        output.versions.append(version)
        
        return output
    
    def format_text(self,
                    content: str,
                    max_width: int = 80,
                    indent: int = 0) -> str:
        """
        格式化文本
        
        Args:
            content: 内容
            max_width: 最大宽度
            indent: 缩进
            
        Returns:
            str: 格式化后的文本
        """
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            if len(line) <= max_width:
                formatted_lines.append(' ' * indent + line)
            else:
                # 自动换行
                words = line.split()
                current_line = ' ' * indent
                
                for word in words:
                    if len(current_line) + len(word) + 1 <= max_width:
                        current_line += word + ' '
                    else:
                        formatted_lines.append(current_line.rstrip())
                        current_line = ' ' * indent + word + ' '
                
                if current_line.strip():
                    formatted_lines.append(current_line.rstrip())
        
        return '\n'.join(formatted_lines)
    
    def create_summary(self,
                       content: str,
                       max_length: int = 200) -> str:
        """
        创建摘要
        
        Args:
            content: 内容
            max_length: 最大长度
            
        Returns:
            str: 摘要
        """
        if len(content) <= max_length:
            return content
        
        # 在句子边界截断
        truncated = content[:max_length]
        last_period = max(truncated.rfind('.'), truncated.rfind('。'),
                         truncated.rfind('!'), truncated.rfind('！'))
        
        if last_period > max_length * 0.5:
            return truncated[:last_period + 1]
        
        return truncated + "..."


class CodeGenerator:
    """代码生成器"""
    
    def __init__(self):
        self._language_patterns = {
            CodeLanguage.PYTHON: {
                "comment": "#",
                "block_comment": ('"""', '"""'),
                "extension": ".py"
            },
            CodeLanguage.JAVASCRIPT: {
                "comment": "//",
                "block_comment": ("/*", "*/"),
                "extension": ".js"
            },
            CodeLanguage.JAVA: {
                "comment": "//",
                "block_comment": ("/*", "*/"),
                "extension": ".java"
            },
            CodeLanguage.SQL: {
                "comment": "--",
                "block_comment": ("/*", "*/"),
                "extension": ".sql"
            },
            CodeLanguage.BASH: {
                "comment": "#",
                "block_comment": None,
                "extension": ".sh"
            }
        }
        logger.info("CodeGenerator initialized")
    
    def generate(self,
                 code: str,
                 language: CodeLanguage = CodeLanguage.PYTHON,
                 title: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> GeneratedOutput:
        """
        生成代码输出
        
        Args:
            code: 代码内容
            language: 代码语言
            title: 标题
            metadata: 元数据
            
        Returns:
            GeneratedOutput: 生成的输出
        """
        output = GeneratedOutput(
            output_type=OutputType.CODE,
            format=OutputFormat.FORMATTED,
            content=code,
            code_language=language,
            code_title=title,
            metadata=metadata or {}
        )
        
        version = OutputVersion(
            content=code,
            change_description="Initial code generation"
        )
        output.versions.append(version)
        
        return output
    
    def add_comments(self,
                     code: str,
                     language: CodeLanguage,
                     comments: Dict[int, str]) -> str:
        """
        添加注释
        
        Args:
            code: 代码
            language: 语言
            comments: {行号: 注释}
            
        Returns:
            str: 添加注释后的代码
        """
        pattern = self._language_patterns.get(language, {"comment": "#"})
        comment_prefix = pattern["comment"]
        
        lines = code.split('\n')
        for line_num, comment in sorted(comments.items(), reverse=True):
            if 0 <= line_num < len(lines):
                lines.insert(line_num, f"{comment_prefix} {comment}")
        
        return '\n'.join(lines)
    
    def wrap_in_codeblock(self,
                          code: str,
                          language: CodeLanguage = CodeLanguage.TEXT) -> str:
        """
        包装为代码块
        
        Args:
            code: 代码
            language: 语言
            
        Returns:
            str: Markdown代码块
        """
        lang = language.value if language else ""
        return f"```{lang}\n{code}\n```"
    
    def extract_code_from_markdown(self, text: str) -> List[Dict[str, Any]]:
        """
        从Markdown提取代码块
        
        Args:
            text: Markdown文本
            
        Returns:
            List[Dict]: 代码块列表
        """
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        results = []
        for lang, code in matches:
            results.append({
                "language": lang or "text",
                "code": code.strip()
            })
        
        return results


class MarkdownGenerator:
    """Markdown生成器"""
    
    def __init__(self):
        logger.info("MarkdownGenerator initialized")
    
    def generate(self,
                 content: str,
                 title: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> GeneratedOutput:
        """
        生成Markdown输出
        
        Args:
            content: 内容
            title: 标题
            metadata: 元数据
            
        Returns:
            GeneratedOutput: 生成的输出
        """
        if title:
            full_content = f"# {title}\n\n{content}"
        else:
            full_content = content
        
        output = GeneratedOutput(
            output_type=OutputType.MARKDOWN,
            format=OutputFormat.FORMATTED,
            content=full_content,
            metadata=metadata or {}
        )
        
        version = OutputVersion(
            content=full_content,
            change_description="Initial markdown generation"
        )
        output.versions.append(version)
        
        return output
    
    def create_heading(self, text: str, level: int = 1) -> str:
        """创建标题"""
        return f"{'#' * level} {text}"
    
    def create_list(self,
                    items: List[str],
                    ordered: bool = False) -> str:
        """
        创建列表
        
        Args:
            items: 项目
            ordered: 是否有序
            
        Returns:
            str: Markdown列表
        """
        lines = []
        for i, item in enumerate(items, 1):
            if ordered:
                lines.append(f"{i}. {item}")
            else:
                lines.append(f"- {item}")
        return '\n'.join(lines)
    
    def create_table(self,
                     headers: List[str],
                     rows: List[List[str]]) -> str:
        """
        创建表格
        
        Args:
            headers: 表头
            rows: 行数据
            
        Returns:
            str: Markdown表格
        """
        lines = []
        
        # 表头
        lines.append('| ' + ' | '.join(headers) + ' |')
        lines.append('|' + '|'.join(['---' for _ in headers]) + '|')
        
        # 行
        for row in rows:
            lines.append('| ' + ' | '.join(str(cell) for cell in row) + ' |')
        
        return '\n'.join(lines)
    
    def create_code_block(self,
                          code: str,
                          language: str = "") -> str:
        """创建代码块"""
        return f"```{language}\n{code}\n```"
    
    def create_blockquote(self, text: str) -> str:
        """创建引用块"""
        lines = text.split('\n')
        return '\n'.join(f"> {line}" for line in lines)
    
    def create_link(self, text: str, url: str) -> str:
        """创建链接"""
        return f"[{text}]({url})"
    
    def create_bold(self, text: str) -> str:
        """创建粗体"""
        return f"**{text}**"
    
    def create_italic(self, text: str) -> str:
        """创建斜体"""
        return f"*{text}*"


class OutputQualityChecker:
    """输出质量检查器"""
    
    def __init__(self):
        self._min_length = 10
        self._max_length = 100000
        logger.info("OutputQualityChecker initialized")
    
    def check(self, output: GeneratedOutput) -> QualityCheckResult:
        """
        检查输出质量
        
        Args:
            output: 输出对象
            
        Returns:
            QualityCheckResult: 检查结果
        """
        issues = []
        warnings = []
        suggestions = []
        checks_passed = []
        
        content = output.content
        
        # 长度检查
        if len(content) < self._min_length:
            issues.append(f"Content too short ({len(content)} chars)")
        else:
            checks_passed.append("length_minimum")
        
        if len(content) > self._max_length:
            warnings.append(f"Content very long ({len(content)} chars)")
        
        # 代码特定检查
        if output.output_type == OutputType.CODE:
            code_issues = self._check_code_quality(content, output.code_language)
            issues.extend(code_issues["issues"])
            warnings.extend(code_issues["warnings"])
            suggestions.extend(code_issues["suggestions"])
            checks_passed.extend(code_issues["passed"])
        
        # Markdown特定检查
        if output.output_type == OutputType.MARKDOWN:
            md_issues = self._check_markdown_quality(content)
            issues.extend(md_issues["issues"])
            warnings.extend(md_issues["warnings"])
            suggestions.extend(md_issues["suggestions"])
            checks_passed.extend(md_issues["passed"])
        
        # 通用检查
        if content.strip() != content:
            warnings.append("Content has leading/trailing whitespace")
        else:
            checks_passed.append("no_extra_whitespace")
        
        if '\n\n\n' in content:
            warnings.append("Excessive blank lines")
        
        # 计算分数
        total_checks = len(issues) + len(warnings) + len(checks_passed)
        if total_checks > 0:
            score = len(checks_passed) / total_checks
        else:
            score = 1.0
        
        return QualityCheckResult(
            overall_score=score,
            issues=issues,
            warnings=warnings,
            suggestions=suggestions,
            checks_passed=checks_passed
        )
    
    def _check_code_quality(self,
                            code: str,
                            language: Optional[CodeLanguage]) -> Dict[str, List[str]]:
        """检查代码质量"""
        issues = []
        warnings = []
        suggestions = []
        passed = []
        
        # 检查是否有语法错误（简化）
        if language == CodeLanguage.PYTHON:
            try:
                compile(code, '<string>', 'exec')
                passed.append("python_syntax")
            except SyntaxError as e:
                issues.append(f"Python syntax error: {e}")
        
        # 检查行长度
        long_lines = [i for i, line in enumerate(code.split('\n'), 1) if len(line) > 120]
        if long_lines:
            warnings.append(f"Long lines found at: {long_lines[:5]}")
        else:
            passed.append("line_length")
        
        # 检查是否有文档字符串
        if language == CodeLanguage.PYTHON and '"""' not in code and "'''" not in code:
            suggestions.append("Consider adding docstrings")
        
        # 检查导入
        if language == CodeLanguage.PYTHON and 'import' not in code:
            suggestions.append("No imports found - verify all dependencies")
        
        return {
            "issues": issues,
            "warnings": warnings,
            "suggestions": suggestions,
            "passed": passed
        }
    
    def _check_markdown_quality(self, content: str) -> Dict[str, List[str]]:
        """检查Markdown质量"""
        issues = []
        warnings = []
        suggestions = []
        passed = []
        
        # 检查标题层次
        headings = re.findall(r'^(#{1,6})\s', content, re.MULTILINE)
        if headings:
            levels = [len(h) for h in headings]
            for i in range(1, len(levels)):
                if levels[i] > levels[i-1] + 1:
                    warnings.append("Heading levels skip")
                    break
            else:
                passed.append("heading_hierarchy")
        
        # 检查未闭合的代码块
        code_blocks = content.count('```')
        if code_blocks % 2 != 0:
            issues.append("Unclosed code block")
        else:
            passed.append("code_blocks_closed")
        
        # 检查空链接
        empty_links = re.findall(r'\[([^\]]*)\]\(\s*\)', content)
        if empty_links:
            warnings.append("Empty links found")
        
        return {
            "issues": issues,
            "warnings": warnings,
            "suggestions": suggestions,
            "passed": passed
        }


class OutputManager:
    """
    输出管理器
    
    统一管理各类输出生成和质量控制。
    """
    
    def __init__(self):
        self.config = get_config()
        self.text_generator = TextGenerator()
        self.code_generator = CodeGenerator()
        self.markdown_generator = MarkdownGenerator()
        self.quality_checker = OutputQualityChecker()
        self._outputs: Dict[str, GeneratedOutput] = {}
        logger.info("OutputManager initialized")
    
    def generate_text(self,
                      content: str,
                      format_type: OutputFormat = OutputFormat.PLAIN,
                      metadata: Optional[Dict[str, Any]] = None) -> GeneratedOutput:
        """生成文本输出"""
        output = self.text_generator.generate(content, format_type, metadata)
        self._outputs[output.id] = output
        return output
    
    def generate_code(self,
                      code: str,
                      language: CodeLanguage = CodeLanguage.PYTHON,
                      title: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> GeneratedOutput:
        """生成代码输出"""
        output = self.code_generator.generate(code, language, title, metadata)
        self._outputs[output.id] = output
        return output
    
    def generate_markdown(self,
                          content: str,
                          title: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> GeneratedOutput:
        """生成Markdown输出"""
        output = self.markdown_generator.generate(content, title, metadata)
        self._outputs[output.id] = output
        return output
    
    def update_output(self,
                      output_id: str,
                      new_content: str,
                      change_description: str = "") -> Optional[GeneratedOutput]:
        """
        更新输出内容（创建新版本）
        
        Args:
            output_id: 输出ID
            new_content: 新内容
            change_description: 变更描述
            
        Returns:
            Optional[GeneratedOutput]: 更新后的输出
        """
        output = self._outputs.get(output_id)
        if not output:
            return None
        
        # 计算差异
        old_content = output.content
        diff = self._compute_diff(old_content, new_content)
        
        # 创建新版本
        version = OutputVersion(
            content=new_content,
            change_description=change_description or "Updated",
            diff_from_previous=diff
        )
        output.versions.append(version)
        output.current_version_index = len(output.versions) - 1
        output.content = new_content
        output.timestamp = datetime.now()
        
        return output
    
    def revert_to_version(self,
                          output_id: str,
                          version_index: int) -> Optional[GeneratedOutput]:
        """
        回退到指定版本
        
        Args:
            output_id: 输出ID
            version_index: 版本索引
            
        Returns:
            Optional[GeneratedOutput]: 回退后的输出
        """
        output = self._outputs.get(output_id)
        if not output:
            return None
        
        if 0 <= version_index < len(output.versions):
            output.current_version_index = version_index
            output.content = output.versions[version_index].content
            
            # 创建回退记录
            version = OutputVersion(
                content=output.content,
                change_description=f"Reverted to version {version_index}"
            )
            output.versions.append(version)
            output.current_version_index = len(output.versions) - 1
        
        return output
    
    def check_quality(self, output_id: str) -> Optional[QualityCheckResult]:
        """检查输出质量"""
        output = self._outputs.get(output_id)
        if not output:
            return None
        
        result = self.quality_checker.check(output)
        output.quality_score = result.overall_score
        output.quality_issues = result.issues
        
        return result
    
    def get_output(self, output_id: str) -> Optional[GeneratedOutput]:
        """获取输出"""
        return self._outputs.get(output_id)
    
    def get_all_outputs(self) -> List[GeneratedOutput]:
        """获取所有输出"""
        return list(self._outputs.values())
    
    def delete_output(self, output_id: str) -> bool:
        """删除输出"""
        if output_id in self._outputs:
            del self._outputs[output_id]
            return True
        return False
    
    def _compute_diff(self, old: str, new: str) -> str:
        """计算差异"""
        diff = difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            lineterm=''
        )
        return ''.join(diff)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self._outputs)
        by_type = {}
        for output in self._outputs.values():
            t = output.output_type.value
            by_type[t] = by_type.get(t, 0) + 1
        
        avg_quality = sum(o.quality_score for o in self._outputs.values()) / max(total, 1)
        
        return {
            "total_outputs": total,
            "by_type": by_type,
            "average_quality": avg_quality
        }
    
    def clear(self) -> None:
        """清空所有输出"""
        self._outputs.clear()
        logger.info("OutputManager cleared")
