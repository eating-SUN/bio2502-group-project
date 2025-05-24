document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const taskId = urlParams.get('task_id');
    
    if (!taskId) {
        showError("未提供任务ID");
        return;
    }

    fetch(`/task/${taskId}`)
        .then(response => {
            if (!response.ok) throw new Error('任务查询失败');
            return response.json();
        })
        .then(data => {
            if (data.status !== 'completed') {
                showError("分析未完成，请稍后刷新");
                return;
            }
            
            // 填充数据
            renderResults(data.result.summary);
        })
        .catch(error => showError(error.message));
});

function renderResults(result) {
    // 填充PRS数据
    document.getElementById('prsScore').textContent = result.prs_score || 'N/A';
    document.getElementById('prsRisk').textContent = result.prs_risk || 'N/A';
    
    // 填充ClinVar数据
    if (result.clinvar_data) {
        const clinvarSection = document.getElementById('clinvarSection');
        clinvarSection.innerHTML = `
            <h5>ClinVar注释</h5>
            <p>临床意义: ${result.clinvar_data.ClinicalSignificance || '未知'}</p>
            <p>表型: ${result.clinvar_data.PhenotypeList || '无记录'}</p>
        `;
    }
    
    // 填充变体表格（示例显示第一个变体）
    if (result.sample_variant) {
        const variant = result.sample_variant;
        document.getElementById('variantTableBody').innerHTML = `
            <tr>
                <td>${variant.chrom || 'N/A'}</td>
                <td>${variant.pos || 'N/A'}</td>
                <td>${variant.ref || 'N/A'}</td>
                <td>${variant.alt || 'N/A'}</td>
            </tr>
        `;
    }
    
    // 显示结果区域
    document.getElementById('loadingMessage').style.display = 'none';
    document.getElementById('resultsContainer').style.display = 'block';
}

function showError(message) {
    document.getElementById('loadingMessage').style.display = 'none';
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.classList.remove('d-none');
}