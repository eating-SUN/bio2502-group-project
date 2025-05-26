// 仅处理纯锚点跳转（无路径前缀）
function navigateTo() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        const href = anchor.getAttribute('href');
        // 仅拦截纯锚点（如 href="#section"），排除带路径的锚点（如 href="/upload#section"）
        if (href.startsWith('#') && href.length > 1) {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                document.querySelector(href).scrollIntoView({
                    behavior: 'smooth'
                });
            });
        }
    });
}

/**
 * 处理VCF文件上传功能
 */
function upload_file(event) {
    event.preventDefault();
    const fileInput = document.getElementById('vcfFile');
    const uploadProgress = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const uploadError = document.getElementById('uploadError');

    // 验证文件选择
    if (!fileInput.files[0]) {
        showError(uploadError, '请选择要上传的VCF文件');
        return;
    }

    const file = fileInput.files[0];
    const MAX_FILE_SIZE = 10 * 1024 * 1024; // 最大允许上传的文件大小（例如：10MB）

    // 检查文件大小
    if (file.size > MAX_FILE_SIZE) {
        showError(uploadError, `文件大小不能超过 ${MAX_FILE_SIZE / (1024 * 1024)} MB`);
        return;
    }

    // 显示进度组件
    uploadProgress.classList.remove('d-none');
    uploadError.classList.add('d-none');

    // 创建XMLHttpRequest实例
    const xhr = new XMLHttpRequest();

    // 处理请求完成
    xhr.onload = () => {
    if (xhr.status >= 200 && xhr.status < 300) {
        const response = JSON.parse(xhr.responseText);
        const taskId = response.task_id;
        checkTaskStatus(taskId); // 开始轮询进度
    } else {
        showError(uploadError, `上传失败，状态码：${xhr.status}`);
    }
};

    // 处理网络错误
    xhr.onerror = () => {
        uploadProgress.classList.add('d-none');
        showError(uploadError, '网络错误，请检查连接后重试');
    };

    // 配置请求
    xhr.open('POST', 'upload', true);

    // 发送请求
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    xhr.send(formData);

}




/**
 * 通用错误显示函数
 * @param {HTMLElement} errorElement 错误容器
 * @param {string} message 错误信息
 */
function showError(errorElement, message) {
    errorElement.textContent = message;
    errorElement.classList.remove('d-none');
    
    // 自动隐藏错误提示（3秒后）
    setTimeout(() => {
        errorElement.classList.add('fade-out');
        setTimeout(() => {
            errorElement.classList.remove('fade-out', 'd-none');
        }, 500);
    }, 3000);
}

/**
 * 提交RSID查询请求
 */
function submitRSID() {
    const rsidInput = document.getElementById('rsid-input');
    const rsidError = document.getElementById('rsidError');
    const queryBtn = rsidInput.closest('div').querySelector('button[type="button"]');

    // 清除历史错误
    rsidError.classList.add('d-none');
    rsidError.textContent = '';
    
    // 获取RSID值
    const rsidValue = rsidInput.value.trim();
    
    // 输入验证
    if (!rsidValue) {
        showError(rsidError, '请输入有效的RSID');
        return;
    }
    if (!/^rs\d+$/.test(rsidValue)) {
        showError(rsidError, 'RSID格式不正确（示例：rs123456）');
        return;
    }

    // 显示加载状态
    queryBtn.disabled = true;
    queryBtn.textContent = '查询中...';

    // 构造请求数据
    const requestData = {
        rsid: rsidValue
    };

    // 发送POST请求
    fetch('/variant_info', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        queryBtn.disabled = false;
        queryBtn.textContent = '查询';
        
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.message || '查询失败');
            });
        }
        return response.json();
    })
    .then(data => {
        // 此处预留结果处理逻辑（根据需求实现）
        console.log('查询成功:', data);
    })
    .catch(error => {
        queryBtn.disabled = false;
        queryBtn.textContent = '查询';
        showError(rsidError, error.message || '网络请求失败');
    });
}
/**
 * 清除RSID输入
 */
function clearInput() {
    document.getElementById('rsid-input').value = '';
}


/**
 * 轮询获取结果
 */
function checkTaskStatus(taskId) {
    const uploadProgress = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    uploadProgress.classList.remove('d-none');

    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/status/${taskId}`);
            const data = await response.json();
            console.log('Task status response:', data);

            // 更新进度条
            if (typeof data.progress === 'number') {
                progressBar.style.width = `${data.progress}%`;
                progressText.textContent = `${data.progress}%`;
                progressBar.classList.remove('progress-bar-indeterminate');
            }
                
                // 显示通知
            if (data.status === 'completed') {
                if (data.result?.variants?.length > 0) {
                    clearInterval(interval);
                    uploadProgress.classList.add('d-none');
                    storeResults(data.result);       
                    } 
                else {
                    showError(document.getElementById('uploadError'), '分析完成，但未检测到有效变异。请检查文件格式。');
                }
            }
            else if (data.status === 'failed') {
                clearInterval(interval);
                uploadProgress.classList.add('d-none');
                showError(document.getElementById('uploadError'),'分析失败');
            }
        } catch (error) {
            clearInterval(interval);
            uploadProgress.classList.add('d-none');
            showError(document.getElementById('uploadError'), '网络错误，请重试');
        }
    }, 2000); // 每2秒查询一次
}

/**
 * 存储分析结果到sessionStorage
 * @param {Array} results 
 */
function storeResults(results) {
    // 仅存储结果到 sessionStorage
    sessionStorage.setItem('vcfResults', JSON.stringify(results));
    
    // 自动跳转到结果页面
    window.location.href = '/results';
}
