import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from fpdf import FPDF
from datetime import datetime
import os
import numpy as np
import tempfile
import io
import base64
import platform

class PDFReport(FPDF):
    def __init__(self, title="变异乳腺癌致病性分析报告"):
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
        
        # 设置Matplotlib中文字体
        self.setup_matplotlib_fonts()
    
    def setup_matplotlib_fonts(self):
        """配置Matplotlib使用中文字体"""
        try:
            # 尝试使用SimHei作为默认中文字体
            if self.fonts_available['SimHei']:
                font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'simhei.ttf')
                if os.path.exists(font_path):
                    # 添加字体到Matplotlib
                    font_prop = fm.FontProperties(fname=font_path)
                    plt.rcParams['font.family'] = font_prop.get_name()
                    plt.rcParams['font.sans-serif'] = [font_prop.get_name()]
                    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
                    print(f"Matplotlib使用字体: {font_prop.get_name()}")
                    return
            
            # 回退到系统支持的中文字体
            system = platform.system()
            if system == "Windows":
                plt.rcParams['font.sans-serif'] = ['SimHei']
            elif system == "Darwin":  # macOS
                plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
            else:  # Linux
                plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
            
            plt.rcParams['axes.unicode_minus'] = False
            print(f"使用系统默认中文字体: {plt.rcParams['font.sans-serif'][0]}")
        except Exception as e:
            print(f"配置Matplotlib字体失败: {e}")
    
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
        self.set_fill_color(240, 240, 240)  # 浅灰色背景
        self.cell(0, 10, title, 0, 1, 'L', True)
        self.ln(3)
        
        # 设置节内容
        self.font_size = 12
        self.set_font_based_on_style('')
        for line in content_lines:
            self.cell(0, 7, line, 0, 1)
        self.ln(5)
        
    def add_table(self, title, headers, rows):
        self.add_section(title, [])
        
        # 表格设置
        col_widths = [25, 20, 15, 20, 20, 35, 25, 30]  # 调整列宽
        
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
            self.set_fill_color(245, 245, 245) if fill else self.set_fill_color(255, 255, 255)
            
            for i, cell in enumerate(row):
                # 特殊处理临床意义和RegulomeDB分数的颜色
                if headers[i] == "临床意义":
                    if "Pathogenic" in cell:
                        self.set_text_color(220, 53, 69)  # 红色
                    elif "Likely pathogenic" in cell:
                        self.set_text_color(255, 193, 7)  # 黄色
                    elif "Benign" in cell:
                        self.set_text_color(40, 167, 69)  # 绿色
                    else:
                        self.set_text_color(0)
                
                if headers[i] == "RegulomeDB分数":
                    if cell and isinstance(cell, str) and cell.startswith(('1', '2')):
                        self.set_text_color(220, 53, 69)  # 红色
                    elif cell and isinstance(cell, str) and cell.startswith(('3', '4')):
                        self.set_text_color(255, 193, 7)  # 黄色
                    elif cell and isinstance(cell, str) and cell.startswith(('5', '6')):
                        self.set_text_color(40, 167, 69)  # 绿色
                    else:
                        self.set_text_color(0)
                
                self.cell(col_widths[i], 8, str(cell), 1, 0, 'C', fill)
                self.set_text_color(0)  # 重置文本颜色
            
            self.ln()
            fill = not fill
        
        self.ln(10)

    def add_protein_section(self, title, protein_info):
        """添加蛋白质变异信息部分"""
        self.add_section(title, [])
        
        # 基本信息
        self.set_font_based_on_style('B')
        self.cell(0, 8, f"蛋白质ID: {protein_info.get('protein_id', 'N/A')}", 0, 1)
        self.cell(0, 8, f"HGVS.p: {protein_info.get('hgvs_p', 'N/A')}", 0, 1)
        self.ln(5)
        
        # 序列对比
        self.set_font_based_on_style('B')
        self.cell(0, 8, "序列对比:", 0, 1)
        
        # 野生型序列
        self.set_font_based_on_style('')
        self.cell(40, 8, "野生型序列:", 0, 0)
        self.set_font('courier', '', 10)  # 使用等宽字体
        self.cell(0, 8, protein_info.get('wt_seq_local', 'N/A'), 0, 1)
        
        # 突变型序列
        self.set_font_based_on_style('')
        self.cell(40, 8, "突变型序列:", 0, 0)
        self.set_font('courier', '', 10)
        self.set_text_color(220, 53, 69)  # 红色
        self.cell(0, 8, protein_info.get('mut_seq_local', 'N/A'), 0, 1)
        self.set_text_color(0)  # 重置文本颜色
        self.ln(5)
        
        # 蛋白质特征变化
        features = protein_info.get('protein_features', {})
        if features:
            self.set_font_based_on_style('B')
            self.cell(0, 8, "蛋白质特征变化:", 0, 1)
            
            feature_names = [
                "分子量变化", "芳香性变化", "不稳定指数变化", 
                "疏水性变化", "等电点变化"
            ]
            feature_keys = [
                "molecular_weight_change", "aromaticity_change", 
                "instability_index_change", "gravy_change", 
                "isoelectric_point_change"
            ]
            
            self.set_font_based_on_style('')
            for name, key in zip(feature_names, feature_keys):
                value = features.get(key, 'N/A')
                change_symbol = ""
                change_color = 0  # 黑色
                
                if isinstance(value, (int, float)):
                    if value > 0:
                        change_symbol = "↑"
                        change_color = 220, 53, 69  # 红色
                    elif value < 0:
                        change_symbol = "↓"
                        change_color = 40, 167, 69  # 绿色
                
                self.cell(60, 8, name, 0, 0)
                self.set_text_color(*change_color)
                self.cell(0, 8, f"{value if isinstance(value, str) else f'{value:.4f}'} {change_symbol}", 0, 1)
                self.set_text_color(0)  # 重置文本颜色
            
            self.ln(5)
    
    def add_chart(self, title, chart_type, chart_data):
        """添加图表到PDF - 使用Agg后端避免线程问题"""
        try:
            # 创建图表 - 使用Agg后端
            plt.switch_backend('Agg')  # 确保使用非交互式后端
            fig, ax = plt.subplots(figsize=(8, 5))
            
            # 设置中文字体
            if self.fonts_available['SimHei']:
                font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'simhei.ttf')
                font_prop = fm.FontProperties(fname=font_path)
                plt.rcParams['font.family'] = font_prop.get_name()
                plt.rcParams['font.sans-serif'] = [font_prop.get_name()]
            else:
                # 尝试使用系统默认中文字体
                system = platform.system()
                if system == "Windows":
                    plt.rcParams['font.sans-serif'] = ['SimHei']
                elif system == "Darwin":  # macOS
                    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
                else:  # Linux
                    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
            
            plt.rcParams['axes.unicode_minus'] = False
            
            if chart_type == "clinvar":
                # 临床意义分布图
                labels = chart_data.get('labels', [])
                sizes = chart_data.get('data', [])
                colors = [
                    '#e74c3c', '#f39c12', '#3498db', 
                    '#2ecc71', '#27ae60', '#95a5a6'
                ]
                
                # 过滤掉大小为0的标签
                filtered_labels = []
                filtered_sizes = []
                filtered_colors = []
                
                for label, size, color in zip(labels, sizes, colors):
                    if size > 0:
                        filtered_labels.append(label)
                        filtered_sizes.append(size)
                        filtered_colors.append(color)
                
                if filtered_sizes:
                    ax.pie(filtered_sizes, labels=filtered_labels, colors=filtered_colors, autopct='%1.1f%%',
                           startangle=90, wedgeprops={'edgecolor': 'white'})
                    ax.axis('equal')  # 确保饼图是圆形
                    ax.set_title('临床意义分布', fontproperties=font_prop if self.fonts_available['SimHei'] else None, fontsize=14)
                else:
                    # 如果没有数据，显示占位符
                    ax.text(0.5, 0.5, '无临床意义数据', 
                            ha='center', va='center', 
                            fontproperties=font_prop if self.fonts_available['SimHei'] else None)
            
            elif chart_type == "prs_distribution":
                # PRS分布图
                labels = chart_data.get('labels', [])
                data = chart_data.get('data', [])
                
                # 排序染色体标签
                try:
                    chrom_order = sorted(labels, key=lambda x: int(x[3:]) if all(x.startswith('chr') for x in labels) else sorted(labels))
                    sorted_data = [data[labels.index(c)] for c in chrom_order]
                except:
                    chrom_order = labels
                    sorted_data = data
                
                if sorted_data:
                    # 创建条形图
                    bars = ax.bar(chrom_order, sorted_data, color='#3498db')
                    ax.set_title('染色体变异分布', fontproperties=font_prop if self.fonts_available['SimHei'] else None, fontsize=14)
                    ax.set_ylabel('变异数量')
                    
                    # 在每个条形上添加数值
                    for bar in bars:
                        height = bar.get_height()
                        ax.annotate(f'{height}',
                                    xy=(bar.get_x() + bar.get_width() / 2, height),
                                    xytext=(0, 3),  # 3 points vertical offset
                                    textcoords="offset points",
                                    ha='center', va='bottom')
                else:
                    # 如果没有数据，显示占位符
                    ax.text(0.5, 0.5, '无变异分布数据', 
                            ha='center', va='center', 
                            fontproperties=font_prop if self.fonts_available['SimHei'] else None)
            
            # 保存图表为图像
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            plt.close(fig)  # 关闭图形释放内存
            
            # 在PDF中添加图像
            self.image(buf, type='png', x=10, w=180)
            self.ln(5)
        except Exception as e:
            print(f"添加图表失败: {e}")
            # 添加错误信息到PDF
            self.set_font_based_on_style('B')
            self.cell(0, 10, f"图表生成失败: {str(e)}", 0, 1)
            self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.font_size = 8
        self.set_font_based_on_style('I')  # 斜体
        self.cell(0, 10, f'第 {self.page_no()} 页', 0, 0, 'C')