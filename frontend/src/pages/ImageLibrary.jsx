import React, { useState, useEffect } from 'react'
import { Card, Input, Select, Row, Col, Pagination, Tag, Image, Empty, Spin, message, Button } from 'antd'
import { SearchOutlined, FilterOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons'
import { useSearchParams } from 'react-router-dom'
import api from '../services/api'
import dayjs from 'dayjs'

const { Search } = Input
const { Option } = Select

const ImageLibrary = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const [images, setImages] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 24,
    total: 0
  })
  const [filters, setFilters] = useState({
    keyword: searchParams.get('keyword') || '',
    source_site: '',
    tag: ''
  })
  const [previewVisible, setPreviewVisible] = useState(false)
  const [previewIndex, setPreviewIndex] = useState(-1) // 当前预览的图片索引，-1表示未预览
  const [pendingPageChange, setPendingPageChange] = useState(null) // 待处理的翻页信息 {direction: 'prev'|'next'}

  // 从URL参数初始化关键字
  useEffect(() => {
    const keywordFromUrl = searchParams.get('keyword')
    if (keywordFromUrl) {
      setFilters(prev => ({ ...prev, keyword: keywordFromUrl }))
    }
  }, [searchParams])

  useEffect(() => {
    fetchData()
  }, [pagination.current, pagination.pageSize, filters])

  // 数据加载完成后，处理待处理的翻页
  useEffect(() => {
    if (images.length > 0 && pendingPageChange) {
      const { direction } = pendingPageChange
      if (direction === 'prev') {
        // 翻到上一页后，预览最后一张
        setPreviewIndex(images.length - 1)
      } else if (direction === 'next') {
        // 翻到下一页后，预览第一张
        setPreviewIndex(0)
      }
      setPreviewVisible(true)
      setPendingPageChange(null)
    }
  }, [images, pendingPageChange])

  // 保存图片（下载）
  const handleSaveImage = async (image) => {
    try {
      const imageUrl = getImageUrl(image)
      if (!imageUrl) {
        message.error('图片URL不存在，无法保存')
        return
      }

      // 创建下载链接
      const link = document.createElement('a')
      link.href = imageUrl
      link.download = image.filename || `image_${image.id}.jpg`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      message.success('图片保存成功')
    } catch (error) {
      message.error('保存图片失败：' + error.message)
      console.error('保存图片错误:', error)
    }
  }

  // 删除图片（移动到回收站）
  const handleDeleteImage = async (image) => {
    try {
      const response = await api.post(`/images/${image.id}/recycle`)
      if (response.code === 200) {
        message.success('图片已移动到回收站')
        // 从列表中移除
        const newImages = images.filter(img => img.id !== image.id)
        setImages(newImages)
        
        // 如果删除的是当前预览的图片，关闭预览或切换到下一张
        if (previewIndex >= 0 && previewIndex < images.length && images[previewIndex].id === image.id) {
          if (newImages.length > 0) {
            // 如果还有图片，切换到下一张（如果删除的是最后一张，切换到上一张）
            const newIndex = previewIndex < newImages.length ? previewIndex : previewIndex - 1
            if (newIndex >= 0) {
              setPreviewIndex(newIndex)
            } else {
              setPreviewVisible(false)
              setPreviewIndex(-1)
            }
          } else {
            setPreviewVisible(false)
            setPreviewIndex(-1)
          }
        }
        
        // 更新总数
        setPagination(prev => ({
          ...prev,
          total: prev.total - 1
        }))
      } else {
        message.error(response.message || '删除失败')
      }
    } catch (error) {
      message.error('删除失败：' + (error.response?.data?.message || error.message))
      console.error('删除图片错误:', error)
    }
  }

  // 键盘事件监听
  useEffect(() => {
    const handleKeyDown = (e) => {
      // 只在预览模式下响应键盘事件
      if (!previewVisible || previewIndex === -1) return
      
      // 检查是否按下了左右键
      if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
        e.preventDefault()
        e.stopPropagation()
        
        if (e.key === 'ArrowLeft') {
          handlePreviousImage()
        } else if (e.key === 'ArrowRight') {
          handleNextImage()
        }
        return
      }

      // 检查是否按下了S键（保存）
      if (e.key === 's' || e.key === 'S') {
        // 避免在输入框中触发
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
          return
        }
        e.preventDefault()
        e.stopPropagation()
        
        const currentImage = images[previewIndex]
        if (currentImage) {
          handleSaveImage(currentImage)
        }
        return
      }

      // 检查是否按下了Delete键（删除）
      if (e.key === 'Delete' || e.key === 'Backspace') {
        // 避免在输入框中触发
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
          return
        }
        e.preventDefault()
        e.stopPropagation()
        
        const currentImage = images[previewIndex]
        if (currentImage) {
          // 直接删除，不需要确认
          handleDeleteImage(currentImage)
        }
        return
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [previewVisible, previewIndex, images, pagination])

  // 处理上一张图片
  const handlePreviousImage = () => {
    if (previewIndex <= 0) {
      // 已经是第一张，尝试翻到上一页
      if (pagination.current > 1) {
        setPreviewVisible(false)
        setPendingPageChange({ direction: 'prev' })
        setPagination(prev => ({
          ...prev,
          current: prev.current - 1
        }))
      }
      return
    }
    
    // 切换到上一张
    setPreviewIndex(previewIndex - 1)
  }

  // 处理下一张图片
  const handleNextImage = () => {
    if (previewIndex >= images.length - 1) {
      // 已经是最后一张，尝试翻到下一页
      const totalPages = Math.ceil(pagination.total / pagination.pageSize)
      if (pagination.current < totalPages) {
        setPreviewVisible(false)
        setPendingPageChange({ direction: 'next' })
        setPagination(prev => ({
          ...prev,
          current: prev.current + 1
        }))
      }
      return
    }
    
    // 切换到下一张
    setPreviewIndex(previewIndex + 1)
  }

  // 打开预览
  const handlePreview = (index) => {
    setPreviewIndex(index)
    setPreviewVisible(true)
  }

  const fetchData = async () => {
    setLoading(true)
    try {
      const params = {
        page: pagination.current,
        page_size: pagination.pageSize,
        keyword: filters.keyword || undefined,
        tag_name: filters.tag || undefined
      }
      
      const response = await api.get('/images', { params })
      
      if (response.code === 200) {
        setImages(response.data.list || [])
        setPagination(prev => ({
          ...prev,
          total: response.data.total || 0
        }))
      } else {
        message.error(response.message || '获取图片列表失败')
      }
    } catch (error) {
      message.error('获取图片列表失败：' + (error.response?.data?.message || error.message))
      console.error('获取图片列表错误:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (value) => {
    setFilters(prev => ({ ...prev, keyword: value }))
    setPagination(prev => ({ ...prev, current: 1 }))
    if (value) {
      setSearchParams({ keyword: value })
    } else {
      setSearchParams({})
    }
  }

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
    setPagination(prev => ({ ...prev, current: 1 }))
  }

  const handlePageChange = (page, pageSize) => {
    setPagination(prev => ({
      ...prev,
      current: page,
      pageSize: pageSize
    }))
  }

  const getImageUrl = (image) => {
    // 优先使用storage_path，通过API接口获取图片内容
    if (image.storage_path) {
      return `/api/images/file/${image.id}/content`
    }
    
    // 如果没有storage_path，返回null（不显示图片）
    return null
  }

  const parseTags = (tagsJson) => {
    if (!tagsJson) return []
    try {
      const tags = JSON.parse(tagsJson)
      return Array.isArray(tags) ? tags : []
    } catch {
      return []
    }
  }

  // 复制到剪贴板
  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text)
      message.success('已复制到剪贴板')
    } catch (error) {
      // 降级方案：使用传统方法
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      document.body.appendChild(textArea)
      textArea.select()
      try {
        document.execCommand('copy')
        message.success('已复制到剪贴板')
      } catch (err) {
        message.error('复制失败')
      }
      document.body.removeChild(textArea)
    }
  }

  return (
    <div>
      {/* 预览箭头按钮 */}
      {previewVisible && previewIndex >= 0 && (
        <>
          {/* 左箭头 */}
          {(previewIndex > 0 || pagination.current > 1) && (
            <Button
              type="primary"
              shape="circle"
              icon={<LeftOutlined />}
              size="large"
              style={{
                position: 'fixed',
                left: '50px',
                top: '50%',
                transform: 'translateY(-50%)',
                zIndex: 1001,
                boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
              }}
              onClick={handlePreviousImage}
            />
          )}
          {/* 右箭头 */}
          {(previewIndex < images.length - 1 || pagination.current < Math.ceil(pagination.total / pagination.pageSize)) && (
            <Button
              type="primary"
              shape="circle"
              icon={<RightOutlined />}
              size="large"
              style={{
                position: 'fixed',
                right: '50px',
                top: '50%',
                transform: 'translateY(-50%)',
                zIndex: 1001,
                boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
              }}
              onClick={handleNextImage}
            />
          )}
        </>
      )}
      <Card
        title="图片库"
        extra={
          <div style={{ display: 'flex', gap: 8 }}>
            <Search
              placeholder="搜索关键词"
              allowClear
              style={{ width: 300 }}
              value={filters.keyword}
              onChange={(e) => {
                const value = e.target.value
                setFilters(prev => ({ ...prev, keyword: value }))
                if (value) {
                  setSearchParams({ keyword: value })
                } else {
                  setSearchParams({})
                }
              }}
              onSearch={handleSearch}
              enterButton={<SearchOutlined />}
            />
            <Select
              placeholder="来源网站"
              allowClear
              style={{ width: 150 }}
              onChange={(value) => handleFilterChange('source_site', value)}
            >
              <Option value="xiaohongshu">小红书</Option>
              <Option value="douyin">抖音</Option>
            </Select>
          </div>
        }
      >
        <Spin spinning={loading}>
          {images.length === 0 ? (
            <Empty description="暂无图片" />
          ) : (
            <>
              <Row gutter={[16, 16]}>
                {images.map((image) => {
                  const tags = parseTags(image.hash_tags_json)
                  const imageUrl = getImageUrl(image)
                  
                  return (
                    <Col key={image.id} xs={12} sm={8} md={6} lg={4} xl={4}>
                      <Card
                        hoverable
                        cover={
                          <div style={{ 
                            width: '100%', 
                            height: 200, 
                            overflow: 'hidden',
                            backgroundColor: '#f5f5f5',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                          }}>
                            {imageUrl ? (
                              <Image
                                src={imageUrl}
                                alt={image.filename}
                                style={{ 
                                  width: '100%', 
                                  height: '100%', 
                                  objectFit: 'cover',
                                  cursor: 'pointer'
                                }}
                                preview={{
                                  visible: previewVisible && previewIndex === images.findIndex(img => img.id === image.id),
                                  onVisibleChange: (visible) => {
                                    if (!visible) {
                                      setPreviewVisible(false)
                                      setPreviewIndex(-1)
                                    }
                                  },
                                  src: previewVisible && previewIndex >= 0 && previewIndex < images.length 
                                    ? getImageUrl(images[previewIndex]) 
                                    : imageUrl,
                                  mask: '预览'
                                }}
                                onClick={() => {
                                  const index = images.findIndex(img => img.id === image.id)
                                  handlePreview(index)
                                }}
                                onError={() => {
                                  console.error(`图片加载失败 (ID: ${image.id}):`, imageUrl)
                                }}
                              />
                            ) : (
                              <div style={{ color: '#999' }}>无图片</div>
                            )}
                          </div>
                        }
                        bodyStyle={{ padding: 12 }}
                      >
                        <div style={{ marginBottom: 8 }}>
                          <div style={{ 
                            fontSize: 12, 
                            color: '#666',
                            marginBottom: 4,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}>
                            {image.filename || '未命名'}
                          </div>
                          {tags.length > 0 && (
                            <div style={{ marginTop: 4 }}>
                              {tags.slice(0, 2).map((tag, idx) => (
                                <Tag key={idx} size="small" color="blue">
                                  {tag}
                                </Tag>
                              ))}
                              {tags.length > 2 && (
                                <Tag size="small">+{tags.length - 2}</Tag>
                              )}
                            </div>
                          )}
                          {image.keyword && (
                            <div style={{ marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                              <span style={{ fontSize: 11, color: '#999' }}>关键词:</span>
                              <Tag 
                                color="green" 
                                size="small"
                                style={{ 
                                  cursor: 'pointer',
                                  userSelect: 'none'
                                }}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  copyToClipboard(image.keyword)
                                }}
                              >
                                {image.keyword}
                              </Tag>
                            </div>
                          )}
                          {image.created_at && (
                            <div style={{ 
                              fontSize: 11, 
                              color: '#999',
                              marginTop: 4
                            }}>
                              {dayjs(image.created_at).format('YYYY-MM-DD')}
                            </div>
                          )}
                        </div>
                      </Card>
                    </Col>
                  )
                })}
              </Row>
              <div style={{ marginTop: 24, textAlign: 'right' }}>
                <Pagination
                  current={pagination.current}
                  pageSize={pagination.pageSize}
                  total={pagination.total}
                  showSizeChanger
                  showQuickJumper
                  showTotal={(total) => `共 ${total} 张图片`}
                  onChange={handlePageChange}
                  onShowSizeChange={handlePageChange}
                  pageSizeOptions={['12', '24', '48', '96']}
                />
              </div>
            </>
          )}
        </Spin>
      </Card>
    </div>
  )
}

export default ImageLibrary

