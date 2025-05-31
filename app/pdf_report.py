from fpdf import FPDF
from datetime import datetime
import os

class PDFReport(FPDF):
    def __init__(self, title="DNA分析报告"):
        super().__init__()
        # 添加常规字体（宋体）和粗体字体（黑体）
        font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
        simsun_path = os.path.join(font_dir, 'simsun.ttc')
        simhei_path = os.path.join(font_dir, 'simhei.ttf')
        
        # 记录字体是否加载成功
        self.fonts_available = {
            'SimSun': False,
            'SimHei': False
        }
        
        # 存储报告标题
        self.report_title = title
        
        # 添加宋体（常规）
        if os.path.exists(simsun_path):
            try:
                self.add_font('SimSun', '', simsun_path, uni=True)
                self.fonts_available['SimSun'] = True
                print(f"成功加载宋体: {simsun_path}")
            except Exception as e:
                print(f"加载宋体失败: {e}")
        else:
            print(f"警告: 未找到宋体文件 (simsun.ttc) 在 {simsun_path}")
        
        # 添加黑体（粗体）
        if os.path.exists(simhei_path):
            try:
                self.add_font('SimHei', '', simhei_path, uni=True)
                # 将黑体同时注册为粗体字体
                self.add_font('SimHei', 'B', simhei_path, uni=True)
                self.fonts_available['SimHei'] = True
                print(f"成功加载黑体: {simhei_path}")
            except Exception as e:
                print(f"加载黑体失败: {e}")
        else:
            print(f"警告: 未找到黑体文件 (simhei.ttf) 在 {simhei_path}")
        
        # 设置默认字体
        if self.fonts_available['SimSun']:
            self.set_font('SimSun', '', 12)
        else:
            self.set_font("Arial", size=12)
            print("警告: 使用Arial作为默认字体")
        
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        
    def set_font_based_on_style(self, style=''):
        """根据样式选择合适的字体"""
        # 确保字体大小为整数
        font_size = int(self.font_size)
        
        # 优先使用黑体作为粗体
        if style == 'B' and self.fonts_available['SimHei']:
            self.set_font('SimHei', '', font_size)
        # 次优先使用宋体作为粗体
        elif style == 'B' and self.fonts_available['SimSun']:
            self.set_font('SimSun', 'B', font_size)
        # 常规使用宋体
        elif self.fonts_available['SimSun']:
            self.set_font('SimSun', '', font_size)
        # 回退到Arial
        else:
            self.set_font("Arial", style, font_size)
    
    def set_title(self, title):
        # 更新报告标题
        self.report_title = title
        
        self.font_size = 16
        self.set_font_based_on_style('B')
        self.cell(0, 10, title, 0, 1, 'C')
        
        # 设置副标题（日期）
        self.font_size = 10
        self.set_font_based_on_style('')
        
        # 创建日期文本并计算宽度
        date_text = f"生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        date_width = self.get_string_width(date_text) + 12  # 添加一些边距
        
        # 将光标移到右侧
        self.set_x(self.w - date_width)
        self.cell(date_width, 5, date_text, 0, 1)
        
        self.ln(10)
        
    def add_section(self, title, content_lines):
        # 设置节标题
        self.font_size = 14
        self.set_font_based_on_style('B')
        self.cell(0, 10, title, 0, 1)
        
        # 设置节内容
        self.font_size = 12
        self.set_font_based_on_style('')
        for line in content_lines:
            self.cell(0, 7, line, 0, 1)
        self.ln(5)
        
    def add_table(self, title, headers, rows):
        self.add_section(title, [])
        
        # 表格设置
        col_widths = [30, 25, 20, 25, 25, 40]
        
        # 表头
        self.set_fill_color(79, 129, 189)  # 蓝色
        self.set_text_color(255)
        self.font_size = 12
        self.set_font_based_on_style('B')
        
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 10, header, 1, 0, 'C', True)
        self.ln()
        
        # 表格内容
        self.set_text_color(0)
        self.font_size = 10
        self.set_font_based_on_style('')
        fill = False
        
        for row in rows:
            self.set_fill_color(230, 230, 230) if fill else self.set_fill_color(255, 255, 255)
            
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 8, str(cell), 1, 0, 'C', fill)
            
            self.ln()
            fill = not fill
        
        self.ln(10)

    def add_image(self, image_path, width=180):
        self.image(image_path, x=10, y=self.get_y(), w=width)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.font_size = 8
        self.set_font_based_on_style('I')  # 斜体
        self.cell(0, 10, f'第 {self.page_no()} 页', 0, 0, 'C')