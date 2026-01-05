import React, { useState, useEffect } from 'react'
import { Card, Row, Col, Pagination, Tag, Image, Empty, Spin, message, Popconfirm, Button, Space } from 'antd'
import { DeleteOutlined } from '@ant-design/icons'
import api from '../services/api'
import { useSearchParams } from 'react-router-dom'

const StyleImageView = () => {
  const [searchParams] = useSearchParams()
  const [styleId, setStyleId] = useState(null)
  const [styleInfo, setStyleInfo] = useState(null)
  const [images, setImages] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 24,
    total: 0
  })

  useEffect(() => {
    const urlStyleId = searchParams.get('styleId')
    if (urlStyleId) {
      const id = parseInt(urlStyleId)
      if (!isNaN(id)) {
        setStyleId(id)
        fetchStyleInfo(id)
      }
    }
  }, [searchParams])

  useEffect(() => {
    if (styleId) {
      fetchImages()
    } else {
      setImages([])
      setStyleInfo(null)
      setPagination(prev => ({ ...prev, total: 0 }))
    }
  }, [styleId, pagination.current, pagination.pageSize])

  // 获取风格信息
  const fetchStyleInfo = async (id) => {
    try {
      const response = await api.get(`/styles/${id}`)
      if (response.code === 200) {
        setStyleInfo(response.data)
      }
    } catch (error) {
      console.error('获取风格信息失败:', error)
    }
  }

  // 获取图片列表
  const fetchImages = async () => {
    if (!styleId) return
    
    setLoading(true)
    try {
      const params = {
        page: pagination.current,
        page_size: pagination.pageSize
      }
      
      const response = await api.get(`/styles/${styleId}/images`, { params })
      
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

  const handlePageChange = (page, pageSize) => {
    setPagination(prev => ({
      ...prev,
      current: page,
      pageSize: pageSize
    }))
  }

  // 将图片移动到回收站
  const handleRecycleImage = async (imageId) => {
    try {
      const response = await api.post(`/styles/${styleId}/images/${imageId}/recycle`)
      if (response.code === 200) {
        message.success('图片已移动到回收站')
        fetchImages()
        fetchStyleInfo(styleId)
      } else {
        message.error(response.message || '操作失败')
      }
    } catch (error) {
      message.error('操作失败：' + (error.response?.data?.message || error.message))
      console.error('操作错误:', error)
    }
  }

  const getImageUrl = (image) => {
    if (image.storage_path) {
      return `/api/images/file/${image.id}/content`
    }
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

  return (
    <div>
      <Card
        title="风格图片查看"
        extra={
          styleInfo && (
            <div style={{ fontSize: 14, color: '#666' }}>
              共 {styleInfo.image_count || 0} 张图片
            </div>
          )
        }
      >
        {styleId && styleInfo && (
          <>
            <div style={{ marginBottom: 16, padding: 12, backgroundColor: '#f5f5f5', borderRadius: 4 }}>
              <div style={{ fontSize: 16, fontWeight: 'bold', marginBottom: 8 }}>
                {styleInfo.name}
              </div>
              {styleInfo.description && (
                <div style={{ fontSize: 14, color: '#666', marginBottom: 4 }}>
                  {styleInfo.description}
                </div>
              )}
              <div style={{ fontSize: 12, color: '#999' }}>
                图片数量: {styleInfo.image_count || 0}
              </div>
            </div>
          </>
        )}
        
        <Spin spinning={loading}>
          {!styleId ? (
            <Empty description="请先选择一个风格" />
          ) : images.length === 0 ? (
            <Empty description="该风格中暂无图片" />
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
                              />
                            ) : (
                              <div style={{ color: '#999' }}>无图片</div>
                            )}
                          </div>
                        }
                        actions={[
                          <Popconfirm
                            title="确定要将此图片移动到回收站吗？"
                            onConfirm={() => handleRecycleImage(image.id)}
                            okText="确定"
                            cancelText="取消"
                          >
                            <Button
                              type="text"
                              danger
                              icon={<DeleteOutlined />}
                              size="small"
                            >
                              回收站
                            </Button>
                          </Popconfirm>
                        ]}
                      >
                        <Card.Meta
                          title={
                            <div style={{ 
                              fontSize: 12, 
                              overflow: 'hidden', 
                              textOverflow: 'ellipsis', 
                              whiteSpace: 'nowrap' 
                            }}>
                              {image.filename || `图片 ${image.id}`}
                            </div>
                          }
                          description={
                            <div>
                              {tags.length > 0 && (
                                <div style={{ marginTop: 8 }}>
                                  {tags.slice(0, 3).map((tag, idx) => (
                                    <Tag key={idx} size="small" style={{ marginBottom: 4 }}>
                                      {tag}
                                    </Tag>
                                  ))}
                                  {tags.length > 3 && (
                                    <Tag size="small" style={{ marginBottom: 4 }}>
                                      +{tags.length - 3}
                                    </Tag>
                                  )}
                                </div>
                              )}
                              {image.keyword && (
                                <div style={{ fontSize: 11, color: '#999', marginTop: 4 }}>
                                  关键词: {image.keyword}
                                </div>
                              )}
                              {image.aesthetic_scores && image.aesthetic_scores.length > 0 && (
                                <div style={{ marginTop: 8 }}>
                                  {image.aesthetic_scores.map((score, idx) => (
                                    <Tag 
                                      key={idx} 
                                      size="small" 
                                      color={score.evaluator_type === 'artimuse' ? 'blue' : 'green'}
                                      style={{ marginBottom: 4 }}
                                    >
                                      {score.evaluator_type === 'artimuse' ? 'ArtiMuse' : 'Q-Insight'}: {
                                        score.score !== null && score.score !== undefined 
                                          ? score.score.toFixed(2) 
                                          : 'N/A'
                                      }
                                    </Tag>
                                  ))}
                                </div>
                              )}
                            </div>
                          }
                        />
                      </Card>
                    </Col>
                  )
                })}
              </Row>
              
              {pagination.total > 0 && (
                <div style={{ marginTop: 24, textAlign: 'right' }}>
                  <Pagination
                    current={pagination.current}
                    pageSize={pagination.pageSize}
                    total={pagination.total}
                    showSizeChanger
                    showTotal={(total) => `共 ${total} 张图片`}
                    onChange={handlePageChange}
                    onShowSizeChange={handlePageChange}
                  />
                </div>
              )}
            </>
          )}
        </Spin>
      </Card>
    </div>
  )
}

export default StyleImageView

