/**
 * 3D 知识图谱可视化应用
 */

const API_BASE = 'http://localhost:8001';
let graph;
let graphData = { nodes: [], edges: [] };
let isRotating = true;

// 颜色配置
const COLORS = {
    ontology: {
        '免疫球蛋白': '#3b82f6',  // 蓝色
        '过敏原': '#ef4444',      // 红色
        '过敏性疾病': '#f97316',  // 橙色
        '症状': '#eab308',        // 黄色
        '治疗方法': '#22c55e',    // 绿色
        '诊断方法': '#a855f7',    // 紫色
        '细胞': '#ec4899',        // 粉色
        '介质': '#6b7280'         // 灰色
    },
    claim: {
        '支持': '#10b981',
        '反驳': '#ef4444',
        '中立': '#6b7280'
    }
};

// 初始化
async function init() {
    try {
        // 加载图谱数据
        const response = await fetch(`${API_BASE}/api/graph`);
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || '加载数据失败');
        }
        
        graphData = result.data;
        
        // 更新统计信息
        updateStats(result.stats);
        
        // 创建 3D 图谱
        createGraph();
        
        // 隐藏加载提示
        document.getElementById('loading').style.display = 'none';
        
    } catch (error) {
        console.error('初始化失败:', error);
        document.getElementById('loading').innerHTML = `
            <div class="spinner"></div>
            <div>加载失败: ${error.message}</div>
            <div style="font-size: 14px; margin-top: 10px;">请确保 API 服务器正在运行</div>
        `;
    }
}

// 更新统计信息
function updateStats(stats) {
    document.getElementById('ontology-count').textContent = stats.ontology_count || 0;
    document.getElementById('claims-count').textContent = stats.claims_count || 0;
    document.getElementById('edges-count').textContent = stats.edges_count || 0;
    
    // 获取 evidence 数量
    fetch(`${API_BASE}/api/evidence`)
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                document.getElementById('evidence-count').textContent = data.count || 0;
            }
        });
}

// 创建 3D 图谱
function createGraph() {
    const container = document.getElementById('container');
    
    // 初始化 3D Force Graph
    graph = ForceGraph3D()(container)
        .graphData(graphData)
        .nodeId('id')
        .nodeLabel(node => `
            <div style="background: rgba(0,0,0,0.8); color: white; padding: 8px 12px; border-radius: 6px; font-size: 13px;">
                <strong>${node.label || node.name_zh}</strong><br/>
                ${node.type === 'ontology' ? `类别: ${node.category}` : `极性: ${node.polarity || 'N/A'}`}
            </div>
        `)
        .nodeVal(node => node.type === 'ontology' ? 8 : 5)
        .nodeColor(node => {
            if (node.type === 'ontology') {
                return COLORS.ontology[node.category] || '#999';
            } else if (node.type === 'claim') {
                return COLORS.claim[node.polarity] || '#6b7280';
            }
            return '#999';
        })
        .nodeOpacity(0.9)
        .nodeResolution(16)
        .linkSource('source')
        .linkTarget('target')
        .linkColor(link => {
            if (link.type === 'parent_relation') {
                return '#999';
            }
            return '#666';
        })
        .linkOpacity(0.3)
        .linkWidth(1)
        .linkDirectionalParticles(2)
        .linkDirectionalParticleWidth(1.5)
        .linkDirectionalParticleSpeed(0.006)
        .onNodeClick(handleNodeClick)
        .onNodeHover(handleNodeHover)
        .backgroundColor('rgba(0,0,0,0)')
        .enableNodeDrag(false);
    
    // 设置相机位置
    graph.cameraPosition({ z: 300 });
    
    // 自动旋转
    autoRotate();
}

// 自动旋转
function autoRotate() {
    if (!graph || !isRotating) return;
    
    const angle = Date.now() * 0.0001;
    const distance = 300;
    
    graph.cameraPosition({
        x: distance * Math.sin(angle),
        z: distance * Math.cos(angle)
    });
    
    requestAnimationFrame(autoRotate);
}

// 切换旋转
function toggleRotation() {
    isRotating = !isRotating;
    const btn = document.querySelector('#controls button:nth-child(2)');
    btn.textContent = isRotating ? '⏸️ 暂停旋转' : '▶️ 继续旋转';
    
    if (isRotating) {
        autoRotate();
    }
}

// 重置视图
function resetView() {
    if (graph) {
        graph.cameraPosition({ x: 0, y: 0, z: 300 }, { x: 0, y: 0, z: 0 }, 1000);
    }
}

// 处理节点点击
function handleNodeClick(node) {
    showDetail(node);
    
    // 聚焦到节点
    if (graph) {
        const distance = 80;
        const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
        
        graph.cameraPosition(
            {
                x: node.x * distRatio,
                y: node.y * distRatio,
                z: node.z * distRatio
            },
            node,
            1000
        );
    }
}

// 处理节点悬停
function handleNodeHover(node) {
    document.body.style.cursor = node ? 'pointer' : 'default';
}

// 显示详情面板
function showDetail(node) {
    const panel = document.getElementById('detail-panel');
    const content = document.getElementById('detail-content');
    
    let html = `<h3>${node.label || node.name_zh}</h3>`;
    
    if (node.type === 'ontology') {
        html += `
            <div class="detail-field">
                <div class="detail-label">类别</div>
                <div class="detail-value">
                    <span class="badge" style="background: ${COLORS.ontology[node.category] || '#999'}">
                        ${node.category}
                    </span>
                </div>
            </div>
        `;
        
        if (node.description) {
            html += `
                <div class="detail-field">
                    <div class="detail-label">描述</div>
                    <div class="detail-value">${node.description}</div>
                </div>
            `;
        }
        
        html += `
            <div class="detail-field">
                <div class="detail-label">节点 ID</div>
                <div class="detail-value"><code>${node.id}</code></div>
            </div>
        `;
    } else if (node.type === 'claim') {
        html += `
            <div class="detail-field">
                <div class="detail-label">极性</div>
                <div class="detail-value">
                    <span class="badge badge-${node.polarity === '支持' ? 'support' : node.polarity === '反驳' ? 'refute' : 'neutral'}">
                        ${node.polarity}
                    </span>
                </div>
            </div>
        `;
        
        if (node.fullTitle) {
            html += `
                <div class="detail-field">
                    <div class="detail-label">完整标题</div>
                    <div class="detail-value">${node.fullTitle}</div>
                </div>
            `;
        }
    }
    
    content.innerHTML = html;
    panel.classList.add('show');
}

// 关闭详情面板
function closeDetail() {
    document.getElementById('detail-panel').classList.remove('show');
}

// 筛选节点
document.getElementById('node-filter')?.addEventListener('change', (e) => {
    const filterType = e.target.value;
    
    if (filterType === 'all') {
        graph.graphData(graphData);
    } else {
        const filteredNodes = graphData.nodes.filter(n => n.type === filterType);
        const nodeIds = new Set(filteredNodes.map(n => n.id));
        const filteredEdges = graphData.edges.filter(e => 
            nodeIds.has(e.source) && nodeIds.has(e.target)
        );
        
        graph.graphData({
            nodes: filteredNodes,
            edges: filteredEdges
        });
    }
});

// 按类别筛选
document.getElementById('category-filter')?.addEventListener('change', (e) => {
    const category = e.target.value;
    
    if (category === 'all') {
        graph.graphData(graphData);
    } else {
        const filteredNodes = graphData.nodes.filter(n => 
            n.type === 'ontology' && n.category === category
        );
        const nodeIds = new Set(filteredNodes.map(n => n.id));
        const filteredEdges = graphData.edges.filter(e => 
            nodeIds.has(e.source) && nodeIds.has(e.target)
        );
        
        graph.graphData({
            nodes: filteredNodes,
            edges: filteredEdges
        });
    }
});

// 页面加载完成后初始化
window.addEventListener('load', init);
