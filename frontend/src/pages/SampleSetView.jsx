import React, { useState, useEffect } from 'react'
import { Card, Select, Row, Col, Pagination, Tag, Image, Empty, Spin, message, Input, Progress, Divider } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import api from '../services/api'
import dayjs from 'dayjs'
import { useSearchParams } from 'react-router-dom'

const { Option } = Select
const { Search } = Input

const SampleSetView = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const [sampleSets, setSampleSets] = useState([])
  const [selectedSampleSetId, setSelectedSampleSetId] = useState(null)
  const [images, setImages] = useState([])
  const [loading, setLoading] = useState(false)
  const [sampleSetInfo, setSampleSetInfo] = useState(null)
  const [featureDistribution, setFeatureDistribution] = useState([])
  const [loadingDistribution, setLoadingDistribution] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 24,
    total: 0
  })
  const [keyword, setKeyword] = useState('')

  // 获取样本集列表
  useEffect(() => {
    const fetchSampleSets = async () => {
      try {
        const response = await api.get('/sample-sets', { 
          params: { page: 1, page_size: 1000, status: 'active' } 
        })
        if (response.code === 200) {
          setSampleSets(response.data.list || [])
          
          // 如果URL中有sampleSetId参数，自动选择
          const urlSampleSetId = searchParams.get('sampleSetId')
          if (urlSampleSetId) {
            const id = parseInt(urlSampleSetId)
            if (!isNaN(id)) {
              setSelectedSampleSetId(id)
            }
          }
        }
      } catch (error) {
        console.error('获取样本集列表失败:', error)
      }
    }
    fetchSampleSets()
  }, [])

  // 获取图片列表
  useEffect(() => {
    if (selectedSampleSetId) {
      fetchImages()
      fetchFeatureDistribution()
    } else {
      setImages([])
      setSampleSetInfo(null)
      setFeatureDistribution([])
      setPagination(prev => ({ ...prev, total: 0 }))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSampleSetId, pagination.current, pagination.pageSize, keyword])

  // 获取特征分布
  const fetchFeatureDistribution = async () => {
    if (!selectedSampleSetId) return
    
    setLoadingDistribution(true)
    try {
      const response = await api.get(`/sample-sets/${selectedSampleSetId}/feature-distribution`)
      if (response.code === 200) {
        setFeatureDistribution(response.data.distribution || [])
      }
    } catch (error) {
      console.error('获取特征分布失败:', error)
    } finally {
      setLoadingDistribution(false)
    }
  }

  const fetchImages = async () => {
    if (!selectedSampleSetId) return
    
    setLoading(true)
    try {
      const params = {
        page: pagination.current,
        page_size: pagination.pageSize,
        keyword: keyword || undefined
      }
      
      const response = await api.get(`/sample-sets/${selectedSampleSetId}/images`, { params })
      
      if (response.code === 200) {
        setImages(response.data.list || [])
        setSampleSetInfo(response.data.sample_set)
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

  const handleSampleSetChange = (value) => {
    setSelectedSampleSetId(value)
    setPagination(prev => ({ ...prev, current: 1 }))
    setKeyword('')
  }

  const handlePageChange = (page, pageSize) => {
    setPagination(prev => ({
      ...prev,
      current: page,
      pageSize: pageSize
    }))
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
        title="样本集查看"
        extra={
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <Select
              placeholder="请选择样本集"
              style={{ width: 300 }}
              value={selectedSampleSetId}
              onChange={handleSampleSetChange}
              showSearch
              filterOption={(input, option) =>
                (option?.children ?? '').toLowerCase().includes(input.toLowerCase())
              }
            >
              {sampleSets.map(set => (
                <Option key={set.id} value={set.id}>
                  {set.name} ({set.image_count || 0} 张)
                </Option>
              ))}
            </Select>
            {selectedSampleSetId && (
              <Search
                placeholder="搜索图片关键词"
                allowClear
                style={{ width: 300 }}
                value={keyword}
                onChange={(e) => {
                  setKeyword(e.target.value)
                  setPagination(prev => ({ ...prev, current: 1 }))
                }}
                onSearch={(value) => {
                  setKeyword(value)
                  setPagination(prev => ({ ...prev, current: 1 }))
                }}
                enterButton={<SearchOutlined />}
              />
            )}
          </div>
        }
      >
        {selectedSampleSetId && sampleSetInfo && (
          <>
            <div style={{ marginBottom: 16, padding: 12, backgroundColor: '#f5f5f5', borderRadius: 4 }}>
              <div style={{ fontSize: 16, fontWeight: 'bold', marginBottom: 8 }}>
                {sampleSetInfo.name}
              </div>
              {sampleSetInfo.description && (
                <div style={{ fontSize: 14, color: '#666', marginBottom: 4 }}>
                  {sampleSetInfo.description}
                </div>
              )}
              <div style={{ fontSize: 12, color: '#999' }}>
                共 {sampleSetInfo.image_count || 0} 张图片
              </div>
            </div>
            
            {/* 特征分布图 */}
            {featureDistribution.length > 0 && (
              <Card 
                title="特征分布" 
                style={{ marginBottom: 16 }}
                loading={loadingDistribution}
              >
                <Row gutter={[16, 16]}>
                  {featureDistribution.map((feature) => (
                    <Col key={feature.feature_id} xs={24} sm={12} lg={8} xl={6}>
                      <Card size="small" title={feature.feature_name} style={{ height: '100%' }}>
                        {feature.values.length > 0 ? (
                          <div>
                            {feature.values.slice(0, 5).map((item, itemIdx) => {
                              const percentage = feature.total > 0 
                                ? Math.round((item.count / feature.total) * 100) 
                                : 0
                              return (
                                <div key={itemIdx} style={{ marginBottom: 12 }}>
                                  <div style={{ 
                                    display: 'flex', 
                                    justifyContent: 'space-between', 
                                    marginBottom: 4,
                                    fontSize: 12
                                  }}>
                                    <span style={{ 
                                      overflow: 'hidden',
                                      textOverflow: 'ellipsis',
                                      whiteSpace: 'nowrap',
                                      flex: 1,
                                      marginRight: 8
                                    }}>
                                      {item.value}
                                    </span>
                                    <span style={{ color: '#666', minWidth: 60, textAlign: 'right' }}>
                                      {item.count} ({percentage}%)
                                    </span>
                                  </div>
                                  <Progress 
                                    percent={percentage} 
                                    size="small"
                                    strokeColor={{
                                      '0%': '#108ee9',
                                      '100%': '#87d068',
                                    }}
                                  />
                                </div>
                              )
                            })}
                            {feature.values.length > 5 && (
                              <div style={{ fontSize: 12, color: '#999', marginTop: 8, textAlign: 'center' }}>
                                还有 {feature.values.length - 5} 个值...
                              </div>
                            )}
                          </div>
                        ) : (
                          <div style={{ color: '#999', fontSize: 12, textAlign: 'center' }}>
                            暂无数据
                          </div>
                        )}
                      </Card>
                    </Col>
                  ))}
                </Row>
              </Card>
            )}
          </>
        )}
        
        <Spin spinning={loading}>
          {!selectedSampleSetId ? (
            <Empty description="请先选择一个样本集" />
          ) : images.length === 0 ? (
            <Empty description="该样本集中暂无图片" />
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
                            <div style={{ 
                              fontSize: 11, 
                              color: '#999',
                              marginTop: 4
                            }}>
                              关键词: {image.keyword}
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

export default SampleSetView

