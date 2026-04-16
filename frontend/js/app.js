const API_BASE = 'http://localhost:3000/api/v1';
let currentPage = 1;
const pageSize = 50;

function getAuthToken() {
    return localStorage.getItem('sla_token');
}

function getUserRole() {
    return localStorage.getItem('sla_user_role');
}

function getUserName() {
    return localStorage.getItem('sla_user_name');
}

function checkAuth() {
    const token = getAuthToken();
    if (!token && !window.location.pathname.includes('login.html')) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

function logout() {
    localStorage.removeItem('sla_token');
    localStorage.removeItem('sla_user_role');
    localStorage.removeItem('sla_user_name');
    window.location.href = 'login.html';
}

async function authFetch(url, options = {}) {
    const token = getAuthToken();
    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };

    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
        logout();
        throw new Error('Phiên làm việc hết hạn');
    }

    if (response.status === 403) {
        throw new Error('Bạn không có quyền thực hiện chức năng này');
    }

    return response;
}

function updateUIForRole() {
    const role = getUserRole();
    const name = getUserName();

    const sidebar = document.querySelector('.sidebar');
    const footer = document.querySelector('.sidebar-footer');

    let profile = document.querySelector('.user-profile');
    if (!profile) {
        profile = document.createElement('div');
        profile.className = 'user-profile';
        sidebar.insertBefore(profile, sidebar.querySelector('.sidebar-nav'));
    }

    const initials = name ? name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() : 'U';
    const roleLabel = role === 'manager' ? 'Quản lý' : 'Nhân viên';

    profile.innerHTML = `
        <div class="user-avatar">${initials}</div>
        <div class="user-info">
            <div class="user-name">${name}</div>
            <div class="user-role">${roleLabel}</div>
        </div>
    `;

    if (!document.getElementById('logoutBtnFooter')) {
        const logoutDiv = document.createElement('div');
        logoutDiv.style.marginTop = '12px';
        logoutDiv.innerHTML = `
            <button class="btn btn-outline btn-sm logout-btn" id="logoutBtnFooter" onclick="logout()" style="width: 100%">
                🚪 Đăng xuất
            </button>
        `;
        footer.appendChild(logoutDiv);
    }

    if (role === 'staff') {
        const staffOnlyPages = ['predict'];
        const managerOnlyItems = ['nav-dashboard', 'nav-packages', 'nav-applications', 'nav-ml-management'];

        managerOnlyItems.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });

        document.querySelectorAll('.nav-section').forEach(section => {
            const title = section.querySelector('.nav-section-title').textContent;
            if (title === 'Quản lý' || title === 'Hệ thống') {
                const visibleButtons = Array.from(section.querySelectorAll('.nav-item')).filter(b => b.style.display !== 'none');
                if (visibleButtons.length === 0) section.style.display = 'none';
            }
        });
    }
}

function showPage(pageId) {
    if (!checkAuth()) return;

    const role = getUserRole();
    if (role === 'staff' && pageId !== 'predict') {
        showToast('Bạn không có quyền truy cập trang này', 'error');
        return;
    }

    document.querySelectorAll('.page-content').forEach(p => {
        p.classList.add('hidden');
    });
    const page = document.getElementById(`page-${pageId}`);
    if (page) {
        page.classList.remove('hidden');
        page.classList.add('fade-in');
    }

    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const navItem = document.getElementById(`nav-${pageId}`);
    if (navItem) navItem.classList.add('active');
    const titles = {
        'predict': '🎯 Dự báo gói vay phù hợp',
        'dashboard': '📊 Dashboard',
        'packages': '📦 Quản lý gói vay',
        'applications': '📋 Hồ sơ vay',
        'ml-management': '🤖 Quản lý ML Models',
    };
    document.getElementById('pageTitle').textContent = titles[pageId] || '';

    if (pageId === 'dashboard') loadDashboard();
    if (pageId === 'packages') loadPackages();
    if (pageId === 'applications') loadApplications();
    if (pageId === 'ml-management') loadMLStatus();
    document.getElementById('sidebar').classList.remove('open');
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = { success: '✅', error: '❌', info: 'ℹ️' };
    toast.innerHTML = `
        <span style="font-size:18px;">${icons[type] || icons.info}</span>
        <span style="font-size:14px; color: var(--text-secondary);">${message}</span>
    `;

    container.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'slideInRight 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function formatMoney(amount) {
    return new Intl.NumberFormat('vi-VN').format(amount);
}

function formatPurpose(purpose) {
    const map = {
        'bds': '🏠 Bất động sản',
        'o_to': '🚗 Ô tô',
        'tieu_dung': '🛍️ Tiêu dùng',
        'kinh_doanh': '💼 Kinh doanh',
    };
    return map[purpose] || purpose;
}

function formatPurposeShort(purpose) {
    const map = {
        'bds': 'BĐS',
        'o_to': 'Ô tô',
        'tieu_dung': 'Tiêu dùng',
        'kinh_doanh': 'Kinh doanh',
    };
    return map[purpose] || purpose;
}

async function handlePredict(event) {
    event.preventDefault();

    const btn = document.getElementById('predictBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Đang phân tích...';

    const data = {
        cccd: document.getElementById('cccd').value,
        age: parseInt(document.getElementById('age').value),
        gender: document.getElementById('gender').value,
        marital_status: document.getElementById('maritalStatus').value,
        monthly_income: parseFloat(document.getElementById('monthlyIncome').value),
        loan_amount: parseFloat(document.getElementById('loanAmount').value),
        purpose: document.getElementById('purpose').value,
        loan_term_months: parseInt(document.getElementById('loanTerm').value),
        living_expenses: parseFloat(document.getElementById('livingExpenses').value),
        current_debt: parseFloat(document.getElementById('currentDebt').value),
        asset_value: parseFloat(document.getElementById('assetValue').value),
        dependents: parseInt(document.getElementById('dependents').value),
        housing_status: document.getElementById('housingStatus').value,
        collateral_assets: document.getElementById('collateralAssets').value,
        repayment_method: document.getElementById('repaymentMethod').value,
    };

    try {
        const response = await authFetch(`${API_BASE}/predictions/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Lỗi dự báo');
        }

        const result = await response.json();
        displayPredictionResults(result);
        showToast('Dự báo thành công!', 'success');

    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '🎯 Dự báo gói vay phù hợp';
    }
}

function displayPredictionResults(result) {
    const container = document.getElementById('recommendationsContainer');
    const assessmentBox = document.getElementById('assessmentBox');

    let html = '';
    result.recommendations.forEach((rec, index) => {
        const rankClass = index === 0 ? 'rank-1' : '';
        const riskColorClass = rec.risk_level === 'low' ? 'text-success' :
            rec.risk_level === 'medium' ? 'text-warning' : 'text-danger';

        html += `
            <div class="recommendation-card ${rankClass} slide-up" style="animation-delay: ${index * 0.1}s">
                <div class="rec-header">
                    <div class="rec-title">
                        <span class="rec-name">${rec.package_name}</span>
                        <span class="rec-purpose">${formatPurpose(rec.purpose)}</span>
                    </div>
                    <div class="rec-confidence">
                        <span class="confidence-value">${rec.confidence.toFixed(1)}%</span>
                        <span class="confidence-label">Độ phù hợp</span>
                    </div>
                </div>

                <div class="rec-body">
                    <div class="rec-detail">
                        <span class="detail-label">Lãi suất ban đầu</span>
                        <span class="detail-value">${rec.base_interest_rate}%/năm</span>
                    </div>
                    <div class="rec-detail">
                        <span class="detail-label">Lãi suất thả nổi</span>
                        <span class="detail-value">${rec.floating_rate}%/năm</span>
                    </div>
                    <div class="rec-detail">
                        <span class="detail-label">Ưu đãi</span>
                        <span class="detail-value text-success">${rec.promotion_months > 0 ? rec.promotion_rate + '% x ' + rec.promotion_months + ' tháng' : 'Không'}</span>
                    </div>
                    <div class="rec-detail">
                        <span class="detail-label">Thời hạn</span>
                        <span class="detail-value">${rec.min_term_months} - ${rec.max_term_months} tháng</span>
                    </div>
                    <div class="rec-detail-group" style="background: rgba(59,130,246,0.03); padding: 10px; border-radius: 8px; margin: 8px 0; border: 1px solid rgba(59,130,246,0.1);">
                        <div class="rec-detail" style="margin-bottom: 4px;">
                            <span class="detail-label">Tiền gốc hàng tháng</span>
                            <span class="detail-value" style="font-weight: 600;">${formatMoney(rec.monthly_principal_estimate)} tr</span>
                        </div>
                        <div class="rec-detail" style="margin-bottom: 4px;">
                            <span class="detail-label">Tiền lãi hàng tháng</span>
                            <span class="detail-value" style="font-weight: 600;">${formatMoney(rec.monthly_interest_estimate)} tr</span>
                        </div>
                        <div class="rec-detail" style="border-top: 1px dashed #cbd5e1; padding-top: 4px; margin-top: 4px;">
                            <span class="detail-label" style="font-weight: 700; color: var(--primary-700);">TỔNG CỘNG</span>
                            <span class="detail-value" style="font-weight: 800; color: var(--primary-700); font-size: 1.1em;">${formatMoney(rec.monthly_payment_estimate)} tr</span>
                        </div>
                    </div>
                    <div class="rec-detail">
                        <span class="detail-label">Chỉ số DTI (Nợ/Thu nhập)</span>
                        <span class="detail-value" style="font-weight: 700; color: ${rec.dti < 35 ? '#059669' : rec.dti < 50 ? '#d97706' : '#dc2626'}; text-decoration: underline;">
                            ${rec.dti}%
                        </span>
                    </div>
                    <div class="rec-detail">
                        <span class="detail-label">Phương thức trả nợ</span>
                        <span class="detail-value" style="font-weight: 500; color: var(--primary-600);">
                            ${rec.repayment_method === 'interest_only' ? 'Trả lãi, Gốc cuối kỳ' : 'Trả góp (Gốc+Lãi)'}
                        </span>
                    </div>
                    <div class="rec-detail">
                        <span class="detail-label">Mức rủi ro</span>
                        <span class="risk-badge ${rec.risk_level}">
                            ${rec.risk_level === 'low' ? '✅ Thấp' : rec.risk_level === 'medium' ? '⚠️ Trung bình' : '🔴 Cao'}
                        </span>
                    </div>
                </div>

                <div class="rec-footer">
                    <div class="rec-reason">💡 ${rec.reason}</div>
                    <div class="rec-actions">
                        <button class="btn btn-primary btn-sm apply-btn"
                            data-package-id="${rec.package_id}"
                            data-package-name="${rec.package_name.replace(/"/g, '&quot;')}"
                            data-risk-score="${rec.risk_score}">
                            ✅ Chọn gói này
                        </button>
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;

    container.querySelectorAll('.apply-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const pkgId = parseInt(this.dataset.packageId);
            const pkgName = this.dataset.packageName;
            const riskScore = parseFloat(this.dataset.riskScore);
            applyPackage(pkgId, pkgName, riskScore);
        });
    });

    const avgRisk = result.recommendations.reduce((sum, r) => sum + r.risk_score, 0) / result.recommendations.length;
    const assessClass = avgRisk < 0.3 ? 'good' : avgRisk < 0.6 ? 'medium' : 'bad';
    const assessIcon = avgRisk < 0.3 ? '✅' : avgRisk < 0.6 ? '⚠️' : '🔴';

    assessmentBox.innerHTML = `
        <div class="assessment-box ${assessClass} slide-up">
            <div class="assessment-title">${assessIcon} ${result.overall_risk_assessment}</div>
            <div class="assessment-text">${result.advice}</div>
        </div>
    `;

    document.getElementById('predictionResults').style.display = 'block';
    document.getElementById('predictionResults').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function clearResults() {
    document.getElementById('predictionResults').style.display = 'none';
}

async function applyPackage(packageId, packageName, riskScore) {
    const customerName = document.getElementById('customerName').value;
    const age = parseInt(document.getElementById('age').value);
    const gender = document.getElementById('gender').value;
    const maritalStatus = document.getElementById('maritalStatus').value;
    const monthlyIncome = parseFloat(document.getElementById('monthlyIncome').value);
    const loanAmount = parseFloat(document.getElementById('loanAmount').value);
    const loanTerm = parseInt(document.getElementById('loanTerm').value);
    const purpose = document.getElementById('purpose').value;
    const livingExpenses = parseFloat(document.getElementById('livingExpenses').value);
    const currentDebt = parseFloat(document.getElementById('currentDebt').value);
    const assetValue = parseFloat(document.getElementById('assetValue').value);
    const dependents = parseInt(document.getElementById('dependents').value);
    const housingStatus = document.getElementById('housingStatus').value;
    const collateralAssets = document.getElementById('collateralAssets').value;
    const repaymentMethod = document.getElementById('repaymentMethod').value;

    if (!customerName) {
        showToast('Vui lòng nhập tên khách hàng', 'error');
        return;
    }

    if (!confirm(`Xác nhận tạo hồ sơ vay với gói "${packageName}" cho khách hàng ${customerName}?`)) return;

    try {
        const payload = {
            cccd: document.getElementById('cccd').value,
            customer_name: customerName,
            age: age,
            gender: gender,
            marital_status: maritalStatus,
            monthly_income: monthlyIncome,
            package_id: packageId,
            loan_amount: loanAmount,
            loan_term_months: loanTerm,
            payment_period: 'monthly',
            purpose: purpose,
            living_expenses: livingExpenses,
            current_debt: currentDebt,
            asset_value: assetValue,
            dependents: dependents,
            housing_status: housingStatus,
            collateral_assets: collateralAssets,
            repayment_method: repaymentMethod,
            risk_score: riskScore,
        };

        const response = await authFetch(`${API_BASE}/predictions/apply`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || 'Lỗi tạo hồ sơ');
        }

        showToast(result.message || `Hồ sơ vay #${result.id} đã được tạo thành công!`, 'success');
        console.log('Loan application created:', result);
    } catch (error) {
        console.error('Apply error:', error);
        showToast(error.message, 'error');
    }
}

async function loadDashboard() {
    try {
        const response = await authFetch(`${API_BASE}/dashboard/stats`);
        const data = await response.json();

        const statsHtml = `
            <div class="stat-card blue fade-in">
                <div class="stat-icon">📋</div>
                <div class="stat-value">${data.total_applications}</div>
                <div class="stat-label">Tổng hồ sơ vay</div>
            </div>
            <div class="stat-card green fade-in" style="animation-delay: 0.1s">
                <div class="stat-icon">✅</div>
                <div class="stat-value">${data.approved_count}</div>
                <div class="stat-label">Đã duyệt</div>
            </div>
            <div class="stat-card yellow fade-in" style="animation-delay: 0.2s">
                <div class="stat-icon">⏳</div>
                <div class="stat-value">${data.pending_count}</div>
                <div class="stat-label">Chờ duyệt</div>
            </div>
            <div class="stat-card red fade-in" style="animation-delay: 0.3s">
                <div class="stat-icon">📊</div>
                <div class="stat-value">${data.average_risk_score !== null ? (data.average_risk_score * 100).toFixed(0) + '%' : 'N/A'}</div>
                <div class="stat-label">Rủi ro trung bình</div>
            </div>
        `;
        document.getElementById('dashboardStats').innerHTML = statsHtml;

        renderBarChart('purposeChart', data.applications_by_purpose, {
            'bds': 'BĐS',
            'o_to': 'Ô tô',
            'tieu_dung': 'Tiêu dùng',
            'kinh_doanh': 'Kinh doanh',
        });

        renderBarChart('riskChart', data.risk_distribution, {
            'low': '🟢 Thấp',
            'medium': '🟡 TB',
            'high': '🔴 Cao',
        }, ['#34d399', '#fbbf24', '#f87171']);

    } catch (error) {
        showToast('Lỗi tải dashboard', 'error');
    }
}

function renderBarChart(containerId, data, labelMap, colors) {
    const container = document.getElementById(containerId);
    if (!data || Object.keys(data).length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Chưa có dữ liệu</p></div>';
        return;
    }

    const maxVal = Math.max(...Object.values(data), 1);
    const defaultColors = ['#0772BA', '#338bc7', '#66a9d5', '#99c6e3'];

    let html = '';
    let i = 0;
    for (const [key, value] of Object.entries(data)) {
        const height = (value / maxVal) * 180;
        const color = colors ? colors[i] || defaultColors[i % 4] : defaultColors[i % 4];
        const label = labelMap[key] || key;
        html += `
            <div class="chart-bar" style="height: ${height}px; background: linear-gradient(to top, ${color}88, ${color});">
                <span class="bar-value">${value}</span>
                <span class="bar-label">${label}</span>
            </div>
        `;
        i++;
    }

    container.innerHTML = html;
}

async function loadPackages() {
    try {
        const response = await authFetch(`${API_BASE}/packages/`);
        const packages = await response.json();

        if (!Array.isArray(packages)) {
            console.error('Expected array but got:', packages);
            return;
        }

        let html = '';
        packages.forEach((pkg, index) => {
            html += `
                <div class="package-card fade-in" style="animation-delay: ${index * 0.05}s">
                    <span class="pkg-purpose ${pkg.purpose}">${formatPurposeShort(pkg.purpose)}</span>
                    <div class="pkg-name">${pkg.name}</div>
                    <div class="pkg-desc">${pkg.description || ''}</div>
                    <div class="pkg-details">
                        <div class="pkg-detail-item">
                            <span class="pkg-detail-label">Lãi suất</span>
                            <span class="pkg-detail-value">${pkg.base_interest_rate}%</span>
                        </div>
                        <div class="pkg-detail-item">
                            <span class="pkg-detail-label">Thả nổi</span>
                            <span class="pkg-detail-value">${pkg.floating_rate}%</span>
                        </div>
                        <div class="pkg-detail-item">
                            <span class="pkg-detail-label">Thời hạn</span>
                            <span class="pkg-detail-value">${pkg.min_term_months}-${pkg.max_term_months}T</span>
                        </div>
                        <div class="pkg-detail-item">
                            <span class="pkg-detail-label">Hạn mức</span>
                            <span class="pkg-detail-value">${formatMoney(pkg.min_amount)}-${formatMoney(pkg.max_amount)}tr</span>
                        </div>
                    </div>
                    ${pkg.promotion_months > 0 ? `
                        <div class="promotion-tag">
                            🎉 Ưu đãi ${pkg.promotion_rate}% trong ${pkg.promotion_months} tháng
                        </div>
                    ` : ''}
                </div>
            `;
        });

        document.getElementById('packagesGrid').innerHTML = html;
    } catch (error) {
        showToast('Lỗi tải gói vay', 'error');
    }
}

async function loadApplications() {
    try {
        const tableBody = document.getElementById('applicationsTable');
        const status = document.getElementById('filterStatus').value;
        const skip = (currentPage - 1) * pageSize;
        
        let url = `${API_BASE}/predictions/applications?skip=${skip}&limit=${pageSize}`;
        if (status) url += `&status=${status}`;

        const response = await authFetch(url);
        const data = await response.json();
        
        const apps = data.items || [];
        const total = data.total || 0;
        const totalPages = Math.ceil(total / pageSize);

        // Update UI state
        document.getElementById('totalAppsCount').textContent = total;
        document.getElementById('prevPageBtn').disabled = currentPage === 1;
        document.getElementById('nextPageBtn').disabled = currentPage >= totalPages;
        
        renderPagination(totalPages, currentPage);

        if (!Array.isArray(apps)) {
            tableBody.innerHTML = `<tr><td colspan="11" style="text-align: center; padding: 40px; color: var(--danger);">Lỗi tải dữ liệu</td></tr>`;
            return;
        }

        if (apps.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="11" style="text-align: center; padding: 40px; color: var(--text-muted);">Chưa có hồ sơ vay nào</td></tr>`;
            return;
        }

        let html = '';
        apps.forEach(app => {
            const riskBadge = app.risk_score !== null
                ? `<span class="risk-badge ${app.risk_score < 0.3 ? 'low' : app.risk_score < 0.6 ? 'medium' : 'high'}">
                     ${(app.risk_score * 100).toFixed(0)}%
                   </span>`
                : 'N/A';

            const paymentBadge = app.is_on_time_payment === true
                ? '<span class="status-badge approved">✅ Tốt</span>'
                : app.is_on_time_payment === false
                    ? '<span class="status-badge rejected">🔴 Trễ/Nợ</span>'
                    : '<span class="status-badge pending">⏳ Chưa có</span>';

            html += `
                <tr>
                    <td><strong>#${app.id}</strong></td>
                    <td>
                        <div style="font-weight: 600;">${app.customer_name}</div>
                        <div style="font-size: 10px; color: var(--text-muted);">${app.cccd || 'N/A'}</div>
                    </td>
                    <td>${app.package_name}</td>
                    <td>${formatMoney(app.loan_amount)} tr</td>
                    <td>${app.loan_term_months}T</td>
                    <td>${app.interest_rate}%</td>
                    <td>
                        <span class="badge-compact">
                            ${app.repayment_method === 'interest_only' ? 'Trả lãi' : 'Trả góp'}
                        </span>
                    </td>
                    <td>${riskBadge}</td>
                    <td><span class="status-badge ${app.status}">${app.status === 'pending' ? '⏳ Chờ' :
                app.status === 'approved' ? '✅ Duyệt' : '❌ Từ chối'
            }</span></td>
                    <td>${paymentBadge}</td>
                    <td>
                        <div style="display: flex; gap: 4px;">
                            ${app.is_on_time_payment !== null ? `
                                <span style="font-size: 11px; color: var(--text-muted); font-style: italic;">Hồ sơ đã kết thúc</span>
                            ` : app.status === 'pending' ? `
                                <button class="btn btn-success btn-sm" onclick="updateAppStatus(${app.id}, 'approved')" title="Duyệt">✅</button>
                                <button class="btn btn-danger btn-sm" onclick="updateAppStatus(${app.id}, 'rejected')" title="Từ chối">❌</button>
                            ` : app.status === 'approved' ? `
                                <button class="btn btn-outline btn-sm" onclick="updatePaymentStatus(${app.id}, true)" title="Trả đúng hạn">💰</button>
                                <button class="btn btn-outline btn-sm" onclick="updatePaymentStatus(${app.id}, false)" title="Báo nợ xấu">⚠️</button>
                            ` : `
                                <span style="font-size: 11px; color: var(--danger-500);">Đã từ chối</span>
                            `}
                        </div>
                    </td>
                </tr>
            `;
        });

        document.getElementById('applicationsTable').innerHTML = html;
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function updateAppStatus(appId, status) {
    const label = status === 'approved' ? 'duyệt' : 'từ chối';
    if (!confirm(`Xác nhận ${label} hồ sơ #${appId}?`)) return;

    try {
        const response = await authFetch(`${API_BASE}/predictions/applications/${appId}/status?status=${status}`, {
            method: 'PUT',
        });
        if (!response.ok) throw new Error('Lỗi cập nhật');

        showToast(`Hồ sơ #${appId} đã được ${label}`, 'success');
        loadApplications();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function checkMLStatus() {
    if (getUserRole() === 'staff') {
        const dot = document.getElementById('mlStatusDot');
        const text = document.getElementById('mlStatusText');
        if (dot) dot.classList.add('ready');
        if (text) text.textContent = 'Nhân viên';
        return null;
    }

    try {
        const response = await authFetch(`${API_BASE}/dashboard/ml/status`);
        const data = await response.json();

        const dot = document.getElementById('mlStatusDot');
        const text = document.getElementById('mlStatusText');

        if (data.ready) {
            dot.classList.add('ready');
            text.textContent = 'ML Ready';
        } else {
            dot.classList.remove('ready');
            text.textContent = 'ML chưa sẵn sàng';
        }

        return data;
    } catch (error) {
        const text = document.getElementById('mlStatusText');
        if (text) text.textContent = 'Không kết nối';
        return null;
    }
}

async function loadMLStatus() {
    const data = await checkMLStatus();
    if (!data) {
        document.getElementById('mlModelStatus').innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">❌</div>
                <h3>Không thể kết nối server</h3>
                <p>Đảm bảo backend đang chạy tại localhost:3000</p>
            </div>
        `;
        return;
    }

    const statusHTML = (name, info) => {
        const icon = info.loaded ? '✅' : '❌';
        const statusClass = info.loaded ? 'text-success' : 'text-danger';
        return `
            <div style="display: flex; justify-content: space-between; align-items: center;
                        padding: 16px; border: 1px solid var(--border-color); border-radius: var(--radius-sm);
                        margin-bottom: 12px;">
                <div>
                    <div style="font-weight: 600; font-size: 15px; color: var(--text-primary);">${icon} ${name}</div>
                    <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">
                        ${info.loaded ? 'Đã tải thành công' : 'Chưa được huấn luyện'}
                    </div>
                </div>
                <span class="risk-badge ${info.loaded ? 'low' : 'high'}">
                    ${info.loaded ? 'READY' : 'NOT READY'}
                </span>
            </div>
        `;
    };

    document.getElementById('mlModelStatus').innerHTML =
        statusHTML('Package Recommender', data.package_recommender) +
        statusHTML('Risk Assessor', data.risk_assessor);
}


async function trainFromFile() {
    const fileInput = document.getElementById('trainFile');
    const btn = document.getElementById('trainUploadBtn');
    const resultDiv = document.getElementById('trainUploadResult');

    if (!fileInput.files || fileInput.files.length === 0) {
        showToast('Vui lòng chọn file CSV hoặc Excel', 'error');
        return;
    }

    const file = fileInput.files[0];
    const fileName = file.name.toLowerCase();

    if (!fileName.endsWith('.csv') && !fileName.endsWith('.xlsx') && !fileName.endsWith('.xls')) {
        showToast('Chỉ hỗ trợ file CSV (.csv) hoặc Excel (.xlsx, .xls)', 'error');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Đang upload & huấn luyện...';
    resultDiv.innerHTML = '';

    try {
        const formData = new FormData();
        formData.append('file', file);

        const token = getAuthToken();
        const response = await fetch(`${API_BASE}/dashboard/ml/train-upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData,
        });

        const result = await response.json();

        if (!response.ok) {
            let errorMsg = '';
            if (result.detail && typeof result.detail === 'object') {
                errorMsg = `<strong>${result.detail.message || 'Lỗi'}</strong><br>`;
                if (result.detail.errors) {
                    errorMsg += result.detail.errors.map(e => `❌ ${e}`).join('<br>');
                }
                if (result.detail.warnings && result.detail.warnings.length > 0) {
                    errorMsg += '<br>' + result.detail.warnings.map(w => `⚠️ ${w}`).join('<br>');
                }
            } else {
                errorMsg = result.detail || 'Lỗi huấn luyện từ file';
            }

            resultDiv.innerHTML = `
                <div class="assessment-box bad">
                    <div class="assessment-title">❌ Không thể huấn luyện</div>
                    <div class="assessment-text">${errorMsg}</div>
                </div>
            `;
            showToast('Lỗi huấn luyện từ file', 'error');
            return;
        }

        let warningHtml = '';
        if (result.warnings && result.warnings.length > 0) {
            warningHtml = '<br><br><strong>⚠️ Cảnh báo:</strong><br>' +
                result.warnings.map(w => `• ${w}`).join('<br>');
        }

        resultDiv.innerHTML = `
            <div class="assessment-box good">
                <div class="assessment-title">✅ ${result.message}</div>
                <div class="assessment-text">
                    <strong>Package Recommender:</strong> Accuracy ${(result.package_accuracy * 100).toFixed(1)}%<br>
                    <strong>Risk Assessor:</strong> Accuracy ${(result.risk_accuracy * 100).toFixed(1)}%<br>
                    <strong>Số mẫu đã sử dụng:</strong> ${result.n_samples} records
                    ${warningHtml}
                </div>
            </div>
        `;

        showToast('Huấn luyện từ file thành công!', 'success');
        checkMLStatus();
        loadMLStatus();

    } catch (error) {
        resultDiv.innerHTML = `
            <div class="assessment-box bad">
                <div class="assessment-title">❌ Lỗi</div>
                <div class="assessment-text">${error.message}</div>
            </div>
        `;
        showToast(error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '📁 Upload & Huấn luyện';
    }
}

async function updatePaymentStatus(appId, isOnTime) {
    const label = isOnTime ? 'Trả đúng hạn' : 'Báo nợ xấu';
    if (!confirm(`Xác nhận đánh dấu hồ sơ #${appId} là "${label}"?`)) return;

    try {
        const response = await authFetch(`${API_BASE}/predictions/applications/${appId}/payment?is_on_time=${isOnTime}`, {
            method: 'PUT',
        });
        if (!response.ok) throw new Error('Lỗi cập nhật');

        showToast(`Cập nhật trạng thái thanh toán hồ sơ #${appId} thành công`, 'success');
        loadApplications();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function syncAndTrainDB() {
    const btn = document.getElementById('syncBtn');
    const resultDiv = document.getElementById('syncResult');
    const statusLabel = document.getElementById('syncStatus');

    if (!confirm('Hệ thống sẽ trích xuất dữ liệu từ Database và thực hiện huấn luyện lại Model. Bạn có muốn tiếp tục?')) return;

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Đang đồng bộ & huấn luyện...';
    statusLabel.innerHTML = 'Trạng thái: Đang xử lý...';
    statusLabel.className = 'risk-badge medium';
    resultDiv.innerHTML = '';

    try {
        const response = await authFetch(`${API_BASE}/ml/sync`, { method: 'POST' });
        const result = await response.json();

        if (!response.ok || result.status === 'error') {
            throw new Error(result.message || 'Lỗi đồng bộ');
        }

        resultDiv.innerHTML = `
            <div class="assessment-box good">
                <div class="assessment-title">✅ Đồng bộ & Huấn luyện thành công</div>
                <div class="assessment-text">
                    <strong>Số mẫu sử dụng:</strong> ${result.n_samples} hồ sơ<br>
                    <strong>Package Accuracy:</strong> ${(result.package_accuracy * 100).toFixed(1)}%<br>
                    <strong>Risk Accuracy:</strong> ${(result.risk_accuracy * 100).toFixed(1)}%<br>
                    <strong>Thời gian xử lý:</strong> ${result.duration_sec}s
                </div>
            </div>
        `;
        showToast('Đồng bộ & Huấn luyện hoàn tất!', 'success');
        statusLabel.innerHTML = 'Trạng thái: Hoàn thành';
        statusLabel.className = 'risk-badge low';
        loadMLStatus();
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="assessment-box bad">
                <div class="assessment-title">❌ Lỗi đồng bộ</div>
                <div class="assessment-text">${error.message}</div>
            </div>
        `;
        showToast(error.message, 'error');
        statusLabel.innerHTML = 'Trạng thái: Lỗi';
        statusLabel.className = 'risk-badge high';
    } finally {
        btn.disabled = false;
        btn.innerHTML = '🔄 Đồng bộ & Huấn luyện ngay';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (checkAuth()) {
        updateUIForRole();

        const startPage = localStorage.getItem('sla_start_page') || 'predict';
        localStorage.removeItem('sla_start_page');

        showPage(startPage);
        checkMLStatus();
    }
});

function changePage(delta) {
    currentPage += delta;
    loadApplications();
}

function goToPage(page) {
    currentPage = page;
    loadApplications();
}

function renderPagination(totalPages, current) {
    const container = document.getElementById('pageNumbers');
    if (!container) return;
    
    let html = '';
    const range = 2; // Number of pages to show around current page
    
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= current - range && i <= current + range)) {
            html += `<button class="btn btn-sm ${i === current ? 'btn-primary' : 'btn-outline'}" onclick="goToPage(${i})" style="min-width: 32px; padding: 6px;">${i}</button>`;
        } else if (i === current - range - 1 || i === current + range + 1) {
            html += `<span style="color: var(--text-muted); padding: 0 4px;">...</span>`;
        }
    }
    
    container.innerHTML = html;
}
