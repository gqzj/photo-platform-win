import api from './api'

// 图片抓取相关API
export const imageCaptureService = {
  // 获取抓取列表
  getCaptureList: (params) => api.get('/images/capture', { params }),
  
  // 开始抓取
  startCapture: (data) => api.post('/images/capture/start', data),
  
  // 暂停抓取
  pauseCapture: () => api.post('/images/capture/pause'),
  
  // 停止抓取
  stopCapture: () => api.post('/images/capture/stop')
}

// 图片打标相关API
export const imageTaggingService = {
  // 获取图片列表
  getImageList: (params) => api.get('/images', { params }),
  
  // 获取单个图片详情
  getImageDetail: (id) => api.get(`/images/${id}`),
  
  // 更新图片标签
  updateImageTags: (id, tags) => api.put(`/images/${id}/tags`, { tags }),
  
  // 批量更新标签
  batchUpdateTags: (ids, tags) => api.post('/images/batch-tags', { ids, tags })
}

// 统计分析相关API
export const imageStatisticsService = {
  // 获取统计数据
  getStatistics: (params) => api.get('/statistics', { params }),
  
  // 获取标签统计
  getTagStatistics: () => api.get('/statistics/tags'),
  
  // 获取时间趋势
  getTimeTrend: (params) => api.get('/statistics/trend', { params })
}

