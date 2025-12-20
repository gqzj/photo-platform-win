import React, { useState, useEffect } from 'react'
import { Card, Input, Select, Row, Col, Pagination, Tag, Image, Empty, Spin, message, Button, Popconfirm, Space, Checkbox } from 'antd'
import { SearchOutlined, UndoOutlined } from '@ant-design/icons'
import api from '../services/api'
import dayjs from 'dayjs'

const { Search } = Input
const { Option } = Select

const ImageRecycle = () => {
  const [images, setImages] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedRowKeys, setSelectedRowKeys] = useState([])
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 24,
    total: 0
  })
  const [filters, setFilters] = useState({
    keyword: '',
    cleaning_reason: ''
  })

  useEffect(() => {
    fetchData()
  }, [pagination.current, pagination.pageSize, filters])

  const fetchData = async () => {
    setLoading(true)
    try {
      const params = {
        page: pagination.current,
        page_size: pagination.pageSize,
        keyword: filters.keyword || undefined,
        cleaning_reason: filters.cleaning_reason || undefined
      }
      
      const response = await api.get('/images/recycle', { params })
      
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

  // 还原单张图片
  const handleRestore = async (imageId) => {
    try {
      const response = await api.post(`/images/recycle/${imageId}/restore`)
      if (response.code === 200) {
        message.success('图片还原成功')
        setSelectedRowKeys([])
        fetchData()
      } else {
        message.error(response.message || '还原失败')
      }
    } catch (error) {
      message.error('还原失败：' + (error.response?.data?.message || error.message))
      console.error('还原错误:', error)
    }
  }

  // 批量还原
  const handleBatchRestore = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要还原的图片')
      return
    }
    
    try {
      const response = await api.post('/images/recycle/batch/restore', { ids: selectedRowKeys })
      if (response.code === 200) {
        message.success(response.message || '批量还原成功')
        setSelectedRowKeys([])
        fetchData()
      } else {
        message.error(response.message || '批量还原失败')
      }
    } catch (error) {
      message.error('批量还原失败：' + (error.response?.data?.message || error.message))
      console.error('批量还原错误:', error)
    }
  }

  // 全选/取消全选
  const handleSelectAll = (checked) => {
    if (checked) {
      // 全选当前页的所有图片
      const allIds = images.map(img => img.id)
      setSelectedRowKeys(allIds)
    } else {
      // 取消全选
      setSelectedRowKeys([])
    }
  }

  // 检查是否全选
  const isAllSelected = images.length > 0 && images.every(img => selectedRowKeys.includes(img.id))
  const isIndeterminate = selectedRowKeys.length > 0 && selectedRowKeys.length < images.length

  const getImageUrl = (image) => {
    // 优先使用storage_path，通过API接口获取图片内容
    if (image.storage_path) {
      return `/api/images/recycle/file/${image.id}/content`
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
      <Card
        title="图片回收站"
        extra={
          <Space>
            <Search
              placeholder="搜索关键词"
              allowClear
              style={{ width: 300 }}
              onSearch={handleSearch}
              enterButton={<SearchOutlined />}
            />
            <Select
              placeholder="清洗原因"
              allowClear
              style={{ width: 150 }}
              onChange={(value) => handleFilterChange('cleaning_reason', value)}
            >
              <Option value="no_face">无人脸</Option>
              <Option value="multiple_faces">多人脸</Option>
              <Option value="no_person">无人物</Option>
              <Option value="multiple_persons">多人物</Option>
              <Option value="contains_text">包含文字</Option>
              <Option value="blurry">图片模糊</Option>
            </Select>
            {selectedRowKeys.length > 0 && (
              <Popconfirm
                title={`确定要还原选中的 ${selectedRowKeys.length} 张图片吗？`}
                onConfirm={handleBatchRestore}
                okText="确定"
                cancelText="取消"
              >
                <Button type="primary" icon={<UndoOutlined />}>
                  批量还原 ({selectedRowKeys.length})
                </Button>
              </Popconfirm>
            )}
          </Space>
        }
      >
        <Spin spinning={loading}>
          {images.length === 0 ? (
            <Empty description="暂无图片" />
          ) : (
            <>
              <div style={{ marginBottom: 16 }}>
                <Space>
                  <Checkbox
                    indeterminate={isIndeterminate}
                    checked={isAllSelected}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                  >
                    全选当前页 ({images.length} 张)
                  </Checkbox>
                  <span>已选择 {selectedRowKeys.length} 张图片</span>
                  {selectedRowKeys.length > 0 && (
                    <Button size="small" onClick={() => setSelectedRowKeys([])}>
                      取消选择
                    </Button>
                  )}
                </Space>
              </div>
              <Row gutter={[16, 16]}>
                {images.map((image) => {
                  const tags = parseTags(image.hash_tags_json)
                  const imageUrl = getImageUrl(image)
                  const isSelected = selectedRowKeys.includes(image.id)
                  
                  return (
                    <Col key={image.id} xs={12} sm={8} md={6} lg={4} xl={4}>
                      <div
                        style={{
                          border: isSelected ? '2px solid #1890ff' : '2px solid transparent',
                          borderRadius: 8,
                          padding: 2,
                          cursor: 'pointer'
                        }}
                        onClick={() => {
                          if (isSelected) {
                            setSelectedRowKeys(selectedRowKeys.filter(id => id !== image.id))
                          } else {
                            setSelectedRowKeys([...selectedRowKeys, image.id])
                          }
                        }}
                      >
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
                            justifyContent: 'center',
                            position: 'relative'
                          }}>
                            {imageUrl ? (
                              <Image
                                src={imageUrl}
                                alt={image.filename}
                                style={{ 
                                  width: '100%', 
                                  height: '100%', 
                                  objectFit: 'cover' 
                                }}
                                preview={{
                                  mask: '预览'
                                }}
                                onError={() => {
                                  console.error(`图片加载失败 (ID: ${image.id}):`, imageUrl)
                                }}
                              />
                            ) : (
                              <div style={{ color: '#999' }}>无图片</div>
                            )}
                            <div style={{
                              position: 'absolute',
                              top: 8,
                              right: 8,
                              zIndex: 10
                            }}>
                              <Popconfirm
                                title="确定要还原这张图片吗？"
                                onConfirm={() => handleRestore(image.id)}
                                okText="确定"
                                cancelText="取消"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <Button
                                  type="primary"
                                  size="small"
                                  icon={<UndoOutlined />}
                                  style={{ fontSize: 12 }}
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  还原
                                </Button>
                              </Popconfirm>
                            </div>
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
                          {image.cleaning_reason && (
                            <div style={{ marginTop: 4 }}>
                              <Tag size="small" color="red">
                                {image.cleaning_reason === 'no_face' ? '无人脸' :
                                 image.cleaning_reason === 'multiple_faces' ? '多人脸' :
                                 image.cleaning_reason === 'no_person' ? '无人物' :
                                 image.cleaning_reason === 'multiple_persons' ? '多人物' :
                                 image.cleaning_reason === 'contains_text' ? '包含文字' :
                                 image.cleaning_reason === 'blurry' ? '图片模糊' :
                                 image.cleaning_reason}
                              </Tag>
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
                          {image.recycled_at && (
                            <div style={{ 
                              fontSize: 11, 
                              color: '#999',
                              marginTop: 4
                            }}>
                              回收时间: {dayjs(image.recycled_at).format('YYYY-MM-DD HH:mm')}
                            </div>
                          )}
                        </div>
                      </Card>
                      </div>
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

export default ImageRecycle

