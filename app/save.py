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
import re
import matplotlib.table as mtable
import matplotlib as mpl
import textwrap

class PDFReport(FPDF):
    def __init__(self, title="变异乳腺癌致病性分析报告"):
        super().__init__()
        # 添加常规字体（宋体）和粗体字体（黑体）
        font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
        simsun_path = os.path.join(font_dir, 'simsun.ttc')
        simhei_path = os.path.join(font_dir, 'simhei.ttf')
        self.base_line_height = 10
        
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
        """配置Matplotlib使用中文字体 - 更健壮的解决方案"""
        try:
            # 优先使用系统安装的中文字体
            system = platform.system()
            if system == "Windows":
                # Windows系统常见中文字体
                chinese_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi', 'FangSong']
            elif system == "Darwin":  # macOS
                # macOS系统常见中文字体
                chinese_fonts = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC', 'Songti SC']
            else:  # Linux
                # Linux系统常见中文字体
                chinese_fonts = ['WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'AR PL UMing CN', 'Noto Sans CJK SC']
            
            # 检查系统是否安装了这些字体
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            selected_font = None
            
            # 查找第一个可用的中文字体
            for font in chinese_fonts:
                if font in available_fonts:
                    selected_font = font
                    break
            
            # 如果系统没有安装中文字体，尝试使用我们提供的字体
            if not selected_font:
                print("系统未安装常见中文字体，尝试使用本地字体文件")
                font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
                
                # 尝试使用黑体
                simhei_path = os.path.join(font_dir, 'simhei.ttf')
                if os.path.exists(simhei_path):
                    try:
                        # 将字体文件添加到matplotlib字体库
                        fm.fontManager.addfont(simhei_path)
                        selected_font = 'SimHei'
                        print(f"成功添加本地黑体字体: {simhei_path}")
                    except Exception as e:
                        print(f"添加本地黑体字体失败: {e}")
                
                # 如果黑体失败，尝试使用宋体
                if not selected_font:
                    simsun_path = os.path.join(font_dir, 'simsun.ttc')
                    if os.path.exists(simsun_path):
                        try:
                            fm.fontManager.addfont(simsun_path)
                            selected_font = 'SimSun'
                            print(f"成功添加本地宋体字体: {simsun_path}")
                        except Exception as e:
                            print(f"添加本地宋体字体失败: {e}")
            
            # 设置matplotlib使用找到的字体
            if selected_font:
                # 设置全局字体
                plt.rcParams['font.family'] = selected_font
                plt.rcParams['font.sans-serif'] = [selected_font]
                plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
                print(f"Matplotlib使用字体: {selected_font}")
                
                # 检查字体是否支持中文
                test_text = "中文测试"
                try:
                    # 创建一个测试图形来验证字体
                    fig, ax = plt.subplots(figsize=(2, 1))
                    ax.text(0.5, 0.5, test_text, fontsize=12, ha='center')
                    ax.axis('off')
                    buf = io.BytesIO()
                    plt.savefig(buf, format='png', dpi=100)
                    plt.close(fig)
                    print("中文字体测试成功")
                except Exception as e:
                    print(f"中文字体测试失败: {e}")
                    # 回退到英文字体
                    plt.rcParams['font.family'] = 'sans-serif'
                    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
            else:
                print("警告: 未找到可用的中文字体，使用默认英文字体")
                plt.rcParams['font.family'] = 'sans-serif'
                plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
            
            # 确保设置生效
            mpl.rcParams.update(mpl.rcParams)
            
        except Exception as e:
            print(f"配置Matplotlib字体失败: {e}")
            # 回退到英文字体
            plt.rcParams['font.family'] = 'sans-serif'
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    
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
        self.font_size = 12  # 保持字体大小不变
        self.set_font_based_on_style('')
        
        # 计算可用宽度
        available_width = self.w - 2 * self.l_margin  # 减去左右边距
            
        for line in content_lines:
        # 处理空行
            if line.strip() == "":
                self.ln(5)
            else:
                # 计算单元格高度
                cell_height = self.calculate_cell_height(line, self.font_size)
                
                try:
                    # 使用可用宽度和计算出的高度作为 multi_cell 的参数
                    self.multi_cell(available_width, cell_height, line, 0, 'L')
                except Exception as e:
                    print(f"Error rendering line: {line}")
                    raise e
            self.ln(5)

    def add_table(self, title, headers, rows, max_rows=15):
        """添加表格 - 使用Matplotlib生成表格图片"""
        self.add_section(title, [])
        
        # 如果行数超过最大值，截断并添加提示
        if len(rows) > max_rows:
            rows = rows[:max_rows]
            self.set_font_based_on_style('')
            self.cell(0, 8, f"注意：表格只显示前{max_rows}行（共{len(rows)}行）", 0, 1)
            self.ln(5)
        
        # 确保Matplotlib字体设置是最新的
        self.setup_matplotlib_fonts()
        
        # 准备表格数据
        cell_text = [headers] + rows
        
        # 计算表格尺寸
        nrows = len(cell_text)
        ncols = len(headers)
        
        # 设置图像尺寸（根据行列数动态调整）
        fig_height = max(0.4 * nrows + 0.5, 2)  # 基础高度 + 标题空间，最小2英寸
        fig_width = min(10, max(ncols * 1.5, 6))  # 最大宽度限制，最小6英寸
        
        # 创建图像和轴
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        ax.axis('off')
        
        # 创建表格
        table = ax.table(
            cellText=cell_text,
            loc='center',
            cellLoc='center',
            colWidths=[1.0 / ncols] * ncols  # 平均列宽
        )
        
        # 设置表格样式
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)  # 缩放表格以更好地适应
        
        # 设置表头样式
        for i in range(ncols):
            cell = table[0, i]
            cell.set_text_props(weight='bold')  # 粗体
            cell.set_facecolor('#4F81BD')  # 蓝色背景
            cell.set_edgecolor('white')    # 边框颜色
            cell.set_text_props(color='white') # 白色文字
        
        # 设置表格单元格样式
        for i in range(1, nrows):
            for j in range(ncols):
                cell = table[i, j]
                cell.set_edgecolor('#D3D3D3')  # 浅灰色边框
                
                # 交替行颜色
                if i % 2 == 1:
                    cell.set_facecolor('#F0F0F0')
                else:
                    cell.set_facecolor('white')
        
        # 保存表格图片
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        # 在PDF中添加表格图片
        img_width = 180  # 固定宽度（毫米）
        img_height = img_width * fig_height / fig_width  # 保持宽高比
        
        # 检查是否需要分页
        if self.get_y() + img_height > self.page_break_trigger:
            self.add_page()
        
        self.image(buf, type='png', x=10, w=img_width)
        self.ln(5)
    
    def calculate_cell_height(self, text, font_size):
        # 假设每行的高度大约是字体大小的1.2倍
        line_height = font_size * 1.2
        lines = text.count('\n') + 1  # 计算文本中的行数
        return lines * line_height
    
    def _calculate_multi_cell_height(self, text, width, line_height):
        """计算多行文本的高度"""
        if not text:
            return line_height
        
        words = text.split()
        lines = 0
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            if self.get_string_width(test_line) < width:
                current_line = test_line
            else:
                lines += 1
                current_line = word + " "
        
        if current_line:
            lines += 1
        
        return lines * line_height

    def add_protein_section(self, title, protein_info):
        """添加蛋白质变异信息部分"""
        self.add_section(title, [])
        
        # 基本信息（紧凑布局）
        self.set_font('SimHei', '', 12)
        info_text = (
            f"蛋白质ID: {protein_info.get('protein_id', 'N/A')} | "
            f"位置: {protein_info.get('position', 'N/A')} | "
            f"突变类型: {protein_info.get('mutation_type', 'N/A')} | "
            f"氨基酸变化: {protein_info.get('ref_aa', '')} → {protein_info.get('alt_aa', '')}"
        )
        self.multi_cell(0, 8, info_text, 0, 'L')
        self.ln(5)
        
        # 序列对比标题
        self.set_font('SimHei', '', 12)
        self.cell(0, 8, "序列对比:", 0, 1)
        self.ln(2)
        
        # 获取序列数据
        wt_seq = protein_info.get('wt_seq', '')
        mut_seq = protein_info.get('mut_seq', '') if protein_info.get('mut_seq') else ""
        
        # 尝试获取位置信息
        try:
            position = int(protein_info.get('position', 0)) - 1  # 转换为0-based索引
        except:
            position = -1  # 无效位置
        
        # 限制序列显示长度
        MAX_DISPLAY_LENGTH = 20
        
        if len(wt_seq) > MAX_DISPLAY_LENGTH:
            # 截取包含突变位置的区域
            if 0 <= position < len(wt_seq):
                start_idx = max(0, position - MAX_DISPLAY_LENGTH//2)
                end_idx = min(len(wt_seq), position + MAX_DISPLAY_LENGTH//2)
                wt_seq = wt_seq[start_idx:end_idx]
                if mut_seq:
                    mut_seq = mut_seq[start_idx:end_idx]
                # 调整位置索引
                position = position - start_idx
            else:
                # 如果位置无效，只显示开头
                wt_seq = wt_seq[:MAX_DISPLAY_LENGTH]
                if mut_seq:
                    mut_seq = mut_seq[:MAX_DISPLAY_LENGTH]
                position = -1
        
        # 显示野生型序列
        self.set_font('SimSun', '', 10)
        self.cell(0, 8, f"野生型序列 ({len(wt_seq)} aa):", 0, 1)
        
        # 使用等宽字体显示序列
        self.set_font('Courier', '', 10)
        self.multi_cell(
            0,
            8, 
            self._format_sequence(wt_seq, position),
            0, 
            'L'
        )
        self.ln(2)
        
        # 显示突变型序列
        if mut_seq:
            self.set_font('SimSun', '', 10)
            self.cell(0, 8, f"突变型序列 ({len(mut_seq)} aa):", 0, 1)
            self.set_font('Courier', '', 10)
            self.multi_cell(
                0,
                8, 
                self._format_sequence(mut_seq, position),
                0, 
                'L'
            )
        else:
            self.set_font('SimSun', '', 10)
            self.cell(0, 8, "突变型序列: 无数据", 0, 1)
        
        self.ln(5)
        
        # 添加滚动提示（当内容过长时）
        if len(wt_seq) > MAX_DISPLAY_LENGTH:
            self.set_font('SimSun', '', 8)
            self.cell(0, 5, "▶ 序列已截断显示（显示中间区域）", 0, 1)

    def _format_sequence(self, sequence, mut_pos, line_length=80):
        """格式化序列，添加行号和高亮突变位置"""
        if not sequence:
            return ""
        
        formatted = []
        # 将序列分割为多行
        for i in range(0, len(sequence), line_length):
            chunk = sequence[i:i+line_length]
            line_num = i + 1  # 氨基酸位置从1开始
            line_header = f"{line_num:>4} | "
            
            # 处理突变高亮
            if 0 <= mut_pos < len(sequence) and i <= mut_pos < i+line_length:
                pos_in_line = mut_pos - i
                # 在突变位置前后添加标记
                highlighted_chunk = (
                    chunk[:pos_in_line] + 
                    "[" + chunk[pos_in_line] + "]" + 
                    chunk[pos_in_line+1:]
                )
                formatted.append(line_header + highlighted_chunk)
            else:
                formatted.append(line_header + chunk)
        
        return "\n".join(formatted)

    def add_chart(self, chart_data):
        try:
            plt.switch_backend('Agg')
            fig, ax = plt.subplots(figsize=(8, 5))
            
            if chart_data['type'] == 'pie':
                # 饼图生成逻辑
                sizes = chart_data['data']['datasets'][0]['data']
                labels = chart_data['data']['labels']
                colors = chart_data['data']['datasets'][0]['backgroundColor']
                
                # 过滤掉大小为0的标签
                filtered_labels = []
                filtered_sizes = []
                filtered_colors = []
                
                for i, size in enumerate(sizes):
                    if size > 0:
                        filtered_labels.append(labels[i])
                        filtered_sizes.append(size)
                        filtered_colors.append(colors[i])
                
                if filtered_sizes:
                    ax.pie(filtered_sizes, labels=filtered_labels, colors=filtered_colors,
                        autopct=lambda pct: f'{pct:.1f}%' if pct > 5 else '',
                        startangle=90, wedgeprops={'edgecolor': 'white'})
                    ax.axis('equal')
                else:
                    ax.text(0.5, 0.5, '无数据', ha='center', va='center', fontsize=12)
            
            elif chart_data['type'] == 'stacked_bar':
                # 堆叠条形图生成逻辑
                labels = chart_data['data']['labels']
                datasets = chart_data['data']['datasets']
                
                bottom = np.zeros(len(labels))
                
                for dataset in datasets:
                    ax.bar(labels, dataset['data'], bottom=bottom, 
                        color=dataset['backgroundColor'], label=dataset['label'])
                    bottom += np.array(dataset['data'])
                
                ax.set_xlabel('染色体')
                ax.set_ylabel('变异数量')
                ax.legend(title='类别', bbox_to_anchor=(1.05, 1), loc='upper left')
            
            plt.title(chart_data['title'], fontsize=14)
            plt.tight_layout()
            
            # 保存并添加到PDF
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150)
            plt.close(fig)
            
            self.image(buf, type='png', x=self.get_x(), w=90)
            self.ln(70)
            
        except Exception as e:
            print(f"添加图表失败: {e}")
            self.set_font_based_on_style('B')
            self.cell(0, 10, f"图表生成失败: {str(e)}", 0, 1)
    def footer(self):
        self.set_y(-15)
        self.font_size = 8
        self.set_font_based_on_style('I')  # 斜体
        self.cell(0, 10, f'第 {self.page_no()} 页', 0, 0, 'C')

@main.route('/api/report', methods=['GET'])
def generate_report():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({'error': 'Missing task_id'}), 400
    
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Invalid task_id'}), 404
    
    if task['status'] != 'completed':
        return jsonify({'error': 'Task not completed'}), 400
    
    tmp_path = None
    try:
        # 生成PDF报告 - 设置自定义标题
        custom_title = "乳腺癌遗传风险分析报告"
        pdf = pdf_report.PDFReport(title=custom_title)  # 修复初始化参数
        
        # 添加封面标题
        pdf.set_title(custom_title)
        
        # 添加PRS信息
        result = task.get('result', {})
        pdf.add_section("PRS风险评分", [
            f"评分: {result.get('summary',{}).get('prs_score', 'N/A')}",
            f"风险等级: {result.get('summary',{}).get('prs_risk', '未评估')}",
            f"基于 {len(result.get('variants', []))} 个变异计算"
        ])
        
        # 添加神经网络预测信息
        model_score = result.get('summary',{}).get('model_score', 0.0)
        model_risk = result.get('summary',{}).get('model_risk', '未评估')
        pdf.add_section("神经网络预测风险评分", [
        f"评分: {model_score * 100:.2f}%",
        f"风险等级: {model_risk}"
        ])
        
        # 添加变异摘要
        variants = result.get('variants', [])
        
        # 安全地计算各种变异数量
        pathogenic_count = 0
        protein_affecting_count = 0
        regulome_scores = []
        
        for v in variants:
            clinvar_data = v.get('clinvar_data', {})
            # 检查是否存在ClinicalSignificance字段
            if clinvar_data and clinvar_data.get('ClinicalSignificance') == 'Pathogenic':
                pathogenic_count += 1
            
            if v.get('protein_info'):
                protein_affecting_count += 1
            
            regulome_score = v.get('regulome_score', {})
            if isinstance(regulome_score, dict) and 'ranking' in regulome_score:
                regulome_scores.append(regulome_score['ranking'][0])
            
        
        # 计算RegulomeDB分数分布
        regulome_distribution = {}
        for score in regulome_scores:
            regulome_distribution[score] = regulome_distribution.get(score, 0) + 1
        
        pdf.add_section("变异摘要", [
            f"总变异数: {len(variants)}",
            f"致病性变异: {pathogenic_count}",
            f"蛋白质影响变异: {protein_affecting_count}",
            f"高影响RegulomeDB分数 (1-2): {sum(count for score, count in regulome_distribution.items() if score in '12')}",
            f"中等影响RegulomeDB分数 (3-4): {sum(count for score, count in regulome_distribution.items() if score in '34')}",
            f"低影响RegulomeDB分数 (5-6): {sum(count for score, count in regulome_distribution.items() if score in '56')}"
        ])
        
        # 添加详细变异表格
        if variants:
            headers = ["变异ID", "参考序列", "变异序列", "临床意义","基因", "模型预测标签", "模型预测得分", "RegulomeDB分数"]
            rows = []
            for v in variants[:15]:  # 只显示前15个
                var_info = v.get('variant_info', {})
                clinvar_data = v.get('clinvar_data', {})
                regulome_score = v.get('regulome_score', {})
                predict_result = v.get('predict_result', {})
                predict_label = predict_result.get('clnsig_pred', '未知')
                predict_score = predict_result.get('predict_score', 0.0)

                label_translation = {
                    'Benign': '良性',
                    'Likely_benign': '可能良性',
                    'Uncertain_significance': '意义未明',
                    'Likely_pathogenic': '可能致病',
                    'Pathogenic': '致病'
                }
                translated_label = label_translation.get(predict_label, '未知')
                
                # 格式化RegulomeDB分数
                if isinstance(regulome_score, dict) and 'ranking' in regulome_score:
                    regulome_text = f"{regulome_score['ranking']} ({regulome_score.get('probability_score', 'N/A')})"
                else:
                    regulome_text = str(regulome_score)
                
                # 安全地获取各字段值
                rows.append([
                    var_info.get('id', ''),
                    var_info.get('ref', ''),
                    var_info.get('alt', ''),
                    clinvar_data.get('ClinicalSignificance', '未知'),
                    clinvar_data.get('Gene', '-'),  # 添加基因列
                    translated_label,  # 模型预测标签   
                    f"{predict_score:.4f}" if predict_score else 'N/A',  # 模型预测得分
                    regulome_text
                ])
            pdf.add_table("变异列表 (前15个)", headers, rows)
        
        # 添加蛋白质变异信息
        protein_variants = [v for v in variants if v.get('protein_info')]
        if protein_variants:
            pdf.add_section("蛋白质变异信息", [f"共发现 {len(protein_variants)} 个影响蛋白质功能的变异"])
            # 只展示前3个蛋白质变异
            for idx, variant in enumerate(protein_variants[:3]):
                protein_info = variant.get('protein_info', {})
                # 确保有足够的序列信息
                if 'wt_seq' not in protein_info:
                    protein_info['wt_seq'] = "无野生型序列数据"
                if 'mut_seq' not in protein_info:
                    protein_info['mut_seq'] = "无突变型序列数据"
                
                pdf.add_protein_section(f"蛋白质变异 #{idx+1}", protein_info)
        
        # 添加图表 - 使用try-except确保即使图表失败也能生成报告
        try:
            # 临床意义分布图
            clinvar_data = {
            'type': 'pie',
            'title': '临床意义分布',
            'data': {
                'labels': ['Pathogenic', 'Likely pathogenic', 'Uncertain significance', 
                        'Likely benign', 'Benign', 'Unknown'],
                'datasets': [{
                    'data': [0, 0, 0, 0, 0, 0],
                    'backgroundColor': [
                        '#e74c3c', '#f39c12', '#3498db', 
                        '#2ecc71', '#27ae60', '#95a5a6'
                    ]
                }]
            }
        }

        # 模型预测分布图（饼图）
        model_prediction_data = {
            'type': 'pie',
            'title': '模型预测结果分布',
            'data': {
                'labels': ['Pathogenic', 'Likely_pathogenic', 'Uncertain_significance', 
                        'Likely_benign', 'Benign', 'Unknown'],
                'datasets': [{
                    'data': [0, 0, 0, 0, 0, 0],
                    'backgroundColor': [
                        '#e74c3c', '#f39c12', '#3498db', 
                        '#2ecc71', '#27ae60', '#95a5a6'
                    ]
                }]
            }
        }

        # 染色体临床分布图（堆叠条形图）
        clinvar_distribution_data = {
            'type': 'stacked_bar',
            'title': '染色体临床意义分布',
            'data': {
                'labels': [],
                'datasets': []
            }
        }

        # 染色体预测分布图（堆叠条形图）
        chromosome_prediction_data = {
            'type': 'stacked_bar',
            'title': '染色体预测结果分布',
            'data': {
                'labels': [],
                'datasets': []
            }
        }

        # 填充数据
        for v in variants:
            # 临床意义数据
            significance = v.get('clinvar_data', {}).get('ClinicalSignificance', 'Unknown')
            if significance in clinvar_data['data']['labels']:
                index = clinvar_data['data']['labels'].index(significance)
                clinvar_data['data']['datasets'][0]['data'][index] += 1
            
            # 模型预测数据
            prediction = v.get('predict_result', {}).get('clnsig_pred', 'Unknown')
            if prediction in model_prediction_data['data']['labels']:
                index = model_prediction_data['data']['labels'].index(prediction)
                model_prediction_data['data']['datasets'][0]['data'][index] += 1

        # 染色体数据处理
        chromosomes = sorted(set(
            v.get('variant_info', {}).get('chrom', 'Unknown') 
            for v in variants
        ))

        # 临床意义类别
        clinvar_categories = [
            'Pathogenic', 'Likely pathogenic', 'Uncertain significance',
            'Likely benign', 'Benign', 'Unknown'
        ]

        # 预测类别
        prediction_categories = [
            'Pathogenic', 'Likely_pathogenic', 'Uncertain_significance',
            'Likely_benign', 'Benign', 'Unknown'
        ]

        # 为每个染色体创建数据
        for chrom in chromosomes:
            clinvar_counts = {cat: 0 for cat in clinvar_categories}
            prediction_counts = {cat: 0 for cat in prediction_categories}
            
            for v in variants:
                if v.get('variant_info', {}).get('chrom') == chrom:
                    # 临床意义计数
                    sig = v.get('clinvar_data', {}).get('ClinicalSignificance', 'Unknown')
                    if sig in clinvar_counts:
                        clinvar_counts[sig] += 1
                    
                    # 预测结果计数
                    pred = v.get('predict_result', {}).get('clnsig_pred', 'Unknown')
                    if pred in prediction_counts:
                        prediction_counts[pred] += 1
            
            # 添加到数据集
            clinvar_distribution_data['data']['labels'].append(chrom)
            chromosome_prediction_data['data']['labels'].append(chrom)

        # 创建数据集
        clinvar_colors = ['#e74c3c', '#f39c12', '#3498db', '#2ecc71', '#27ae60', '#95a5a6']
        prediction_colors = ['#e74c3c', '#f39c12', '#3498db', '#2ecc71', '#27ae60', '#95a5a6']

        for i, cat in enumerate(clinvar_categories):
            data = []
            for chrom in chromosomes:
                count = 0
                for v in variants:
                    if v.get('variant_info', {}).get('chrom') == chrom:
                        sig = v.get('clinvar_data', {}).get('ClinicalSignificance', 'Unknown')
                        if sig == cat:
                            count += 1
                data.append(count)
            
            clinvar_distribution_data['data']['datasets'].append({
                'label': cat,
                'data': data,
                'backgroundColor': clinvar_colors[i]
            })

        for i, cat in enumerate(prediction_categories):
            data = []
            for chrom in chromosomes:
                count = 0
                for v in variants:
                    if v.get('variant_info', {}).get('chrom') == chrom:
                        pred = v.get('predict_result', {}).get('clnsig_pred', 'Unknown')
                        if pred == cat:
                            count += 1
                data.append(count)
            
            chromosome_prediction_data['data']['datasets'].append({
                'label': cat,
                'data': data,
                'backgroundColor': prediction_colors[i]
            })
        
        charts = [
            clinvar_data,
            model_prediction_data,
            clinvar_distribution_data,
            chromosome_prediction_data
        ]

        # 每页显示两个图表
        for i in range(0, len(charts), 2):
            pdf.add_page()
            
            # 第一个图表
            pdf.set_y(40)
            pdf.set_font_based_on_style('B')
            pdf.cell(0, 10, charts[i]['title'], 0, 1, 'C')
            pdf.ln(2)
            pdf.add_chart(charts[i])
            
            # 第二个图表（如果有）
            if i+1 < len(charts):
                pdf.set_y(40)
                pdf.set_x(pdf.w / 2 + 10)
                pdf.set_font_based_on_style('B')
                pdf.cell(0, 10, charts[i+1]['title'], 0, 1, 'C')
                pdf.ln(2)
                pdf.set_x(pdf.w / 2 + 10)
                pdf.add_chart(charts[i+1])
        
        
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            pdf.output(tmp.name, 'F')  # 使用output方法保存文件
            tmp_path = tmp.name
        
        return send_file(
            tmp_path,
            as_attachment=True,
            download_name=f'breast_cancer_risk_report_{task_id}.pdf',
            mimetype='application/pdf'
        )
    
    except Exception as e:
        print(f"生成报告失败: {e}")
        traceback.print_exc()
        return jsonify({'error': f'报告生成失败: {str(e)}'}), 500
    
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception as e:
                print(f"删除临时文件失败: {e}")