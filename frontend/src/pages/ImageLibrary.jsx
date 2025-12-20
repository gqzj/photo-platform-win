import React, { useState, useEffect } from 'react'
import { Card, Input, Select, Row, Col, Pagination, Tag, Image, Empty, Spin, message } from 'antd'
import { SearchOutlined, FilterOutlined } from '@ant-design/icons'
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

