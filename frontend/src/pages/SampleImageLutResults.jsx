import React, { useState, useEffect, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Row,
  Col,
  Image,
  Spin,
  message,
  Button,
  Typography,
  Space,
  Tag,
  Select,
  Checkbox
} from 'antd'
import { ArrowLeftOutlined, LikeOutlined, DislikeOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Title, Text } = Typography
const { Option } = Select

const SampleImageLutResults = () => {
  const { imageId } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [originalImage, setOriginalImage] = useState(null)
  const [lutAppliedImages, setLutAppliedImages] = useState([])
  const [sortOrder, setSortOrder] = useState('none') // 'none', 'desc', 'asc'
  const [filters, setFilters] = useState({
    tone: undefined,
    saturation: undefined,
    contrast: undefined
  })
  const [excludeDisliked, setExcludeDisliked] = useState(false)
  const [preferences, setPreferences] = useState({}) // {imageId: isLiked}

  useEffect(() => {
    fetchData()
  }, [imageId, filters, excludeDisliked])

  const fetchData = async () => {
    setLoading(true)
    try {
      // 获取原始图片信息
      const imageResponse = await api.get(`/sample-images/${imageId}`)
      if (imageResponse.code === 200) {
        setOriginalImage(imageResponse.data)
      }

      // 构建查询参数
      const params = { page_size: 1000 } // 获取所有结果
      if (filters.tone) params.tone = filters.tone
      if (filters.saturation) params.saturation = filters.saturation
      if (filters.contrast) params.contrast = filters.contrast
      if (excludeDisliked) params.exclude_disliked = 'true'

      // 获取LUT应用后的图片列表
      const lutResponse = await api.get(`/sample-images/${imageId}/lut-applied-images`, { params })
      if (lutResponse.code === 200) {
        // 后端返回的是数组格式
        const data = lutResponse.data
        const images = Array.isArray(data) ? data : (data?.list || [])
        console.log('LUT应用后的图片数据:', images)
        setLutAppliedImages(images)
        
        // 更新偏好状态
        const prefMap = {}
        images.forEach(img => {
          if (img.preference) {
            prefMap[img.id] = img.preference.is_liked
          }
        })
        setPreferences(prefMap)
      } else {
        message.error(lutResponse.message || '获取LUT结果失败')
      }
    } catch (error) {
      message.error('获取数据失败：' + (error.response?.data?.message || error.message))
      console.error('获取数据错误:', error)
    } finally {
      setLoading(false)
    }
  }

  // 对图片列表进行排序
  const sortedImages = useMemo(() => {
    if (sortOrder === 'none') {
      return lutAppliedImages
    }
    
    const sorted = [...lutAppliedImages].sort((a, b) => {
      const scoreA = a.aesthetic_score?.score ? Number(a.aesthetic_score.score) : -1
      const scoreB = b.aesthetic_score?.score ? Number(b.aesthetic_score.score) : -1
      
      // 没有评分的排在最后
      if (scoreA === -1 && scoreB === -1) return 0
      if (scoreA === -1) return 1
      if (scoreB === -1) return -1
      
      if (sortOrder === 'desc') {
        return scoreB - scoreA // 从高到低
      } else {
        return scoreA - scoreB // 从低到高
      }
    })
    
    return sorted
  }, [lutAppliedImages, sortOrder])

  const handleSortChange = (value) => {
    setSortOrder(value)
  }

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value || undefined
    }))
  }

  const handleClearFilters = () => {
    setFilters({
      tone: undefined,
      saturation: undefined,
      contrast: undefined
    })
  }

  const handlePreference = async (appliedImageId, isLiked) => {
    try {
      const response = await api.post(`/sample-images/lut-applied-images/${appliedImageId}/preference`, {
        is_liked: isLiked
      })
      
      if (response.code === 200) {
        setPreferences(prev => ({
          ...prev,
          [appliedImageId]: isLiked
        }))
        message.success(isLiked ? '已标记为喜欢' : '已标记为不喜欢')
        
        // 如果设置了排除不喜欢，需要重新获取数据
        if (!isLiked && excludeDisliked) {
          fetchData()
        }
      } else {
        message.error(response.message || '操作失败')
      }
    } catch (error) {
      message.error('操作失败：' + (error.response?.data?.message || error.message))
    }
  }

  const handleRemovePreference = async (appliedImageId) => {
    try {
      const response = await api.delete(`/sample-images/lut-applied-images/${appliedImageId}/preference`)
      
      if (response.code === 200) {
        setPreferences(prev => {
          const newPrefs = { ...prev }
          delete newPrefs[appliedImageId]
          return newPrefs
        })
        message.success('已取消标记')
      } else {
        message.error(response.message || '操作失败')
      }
    } catch (error) {
      message.error('操作失败：' + (error.response?.data?.message || error.message))
    }
  }


  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div>
                <Button
                  icon={<ArrowLeftOutlined />}
                  onClick={() => navigate('/lut-analysis/sample-images')}
                  style={{ marginBottom: 16 }}
                >
                  返回
                </Button>
                <Title level={3} style={{ margin: 0 }}>LUT应用结果</Title>
              </div>
              <Select
                value={sortOrder}
                onChange={handleSortChange}
                style={{ width: 200 }}
                placeholder="排序方式"
              >
                <Option value="none">默认排序</Option>
                <Option value="desc">美学评分：从高到低</Option>
                <Option value="asc">美学评分：从低到高</Option>
              </Select>
            </div>
            
            {/* LUT标签筛选 */}
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
              <span style={{ fontWeight: 500 }}>LUT标签筛选：</span>
              <Select
                value={filters.tone}
                onChange={(value) => handleFilterChange('tone', value)}
                style={{ width: 150 }}
                placeholder="色调"
                allowClear
              >
                <Option value="暖调">暖调</Option>
                <Option value="冷调">冷调</Option>
                <Option value="中性调">中性调</Option>
              </Select>
              <Select
                value={filters.saturation}
                onChange={(value) => handleFilterChange('saturation', value)}
                style={{ width: 150 }}
                placeholder="饱和度"
                allowClear
              >
                <Option value="高饱和">高饱和</Option>
                <Option value="中饱和">中饱和</Option>
                <Option value="低饱和">低饱和</Option>
              </Select>
              <Select
                value={filters.contrast}
                onChange={(value) => handleFilterChange('contrast', value)}
                style={{ width: 150 }}
                placeholder="对比度"
                allowClear
              >
                <Option value="高对比">高对比</Option>
                <Option value="中对比">中对比</Option>
                <Option value="低对比">低对比</Option>
              </Select>
              {(filters.tone || filters.saturation || filters.contrast) && (
                <Button onClick={handleClearFilters} size="small">
                  清除筛选
                </Button>
              )}
              <Checkbox
                checked={excludeDisliked}
                onChange={(e) => setExcludeDisliked(e.target.checked)}
                style={{ marginLeft: 16 }}
              >
                排除不喜欢
              </Checkbox>
            </div>
          </div>

          <Spin spinning={loading}>
            <Row gutter={[24, 24]}>
              {/* 原始图片 */}
              <Col xs={24} sm={12} md={8} lg={6}>
                <Card
                  bordered
                  style={{ textAlign: 'center' }}
                >
                  {originalImage && (
                    <>
                      <Image
                        src={`/api/sample-images/${imageId}/content`}
                        alt={originalImage.original_filename}
                        style={{ width: '100%', maxHeight: '400px', objectFit: 'contain' }}
                        preview={true}
                      />
                      <div style={{ marginTop: 12 }}>
                        <Text strong style={{ display: 'block', marginBottom: 8 }}>
                          {originalImage.original_filename}
                        </Text>
                        <Text type="secondary" style={{ fontSize: 14, display: 'block', marginBottom: 4 }}>
                          原始图片
                        </Text>
                      </div>
                    </>
                  )}
                </Card>
              </Col>

              {/* LUT应用后的图片 */}
              {sortedImages.map((appliedImage) => (
                <Col xs={24} sm={12} md={8} lg={6} key={appliedImage.id}>
                  <Card
                    bordered
                    style={{ textAlign: 'center' }}
                  >
                    <Image
                      src={`/api/sample-images/lut-applied-images/${appliedImage.id}/content`}
                      alt={appliedImage.filename}
                      style={{ width: '100%', maxHeight: '400px', objectFit: 'contain' }}
                      preview={true}
                    />
                    <div style={{ marginTop: 12 }}>
                      <Text strong style={{ display: 'block', marginBottom: 8 }}>
                        {appliedImage.filename}
                      </Text>
                      <Text type="secondary" style={{ fontSize: 14, display: 'block', marginBottom: 4 }}>
                        LUT: {appliedImage.lut_file?.original_filename || appliedImage.lut_file?.filename || appliedImage.lut_file_name || '未知'}
                      </Text>
                      <Text type="secondary" style={{ fontSize: 12, display: 'block', color: '#999', marginBottom: 4 }}>
                        类别: {appliedImage.lut_file?.category_name || '未分类'}
                      </Text>
                      {/* LUT标签显示 */}
                      {appliedImage.lut_file?.tag && (
                        <div style={{ marginTop: 4, marginBottom: 4 }}>
                          {appliedImage.lut_file.tag.tone && (
                            <Tag color="orange" style={{ marginRight: 4 }}>
                              色调: {appliedImage.lut_file.tag.tone}
                            </Tag>
                          )}
                          {appliedImage.lut_file.tag.saturation && (
                            <Tag color="blue" style={{ marginRight: 4 }}>
                              饱和度: {appliedImage.lut_file.tag.saturation}
                            </Tag>
                          )}
                          {appliedImage.lut_file.tag.contrast && (
                            <Tag color="purple" style={{ marginRight: 4 }}>
                              对比度: {appliedImage.lut_file.tag.contrast}
                            </Tag>
                          )}
                        </div>
                      )}
                      {appliedImage.aesthetic_score && (
                        <Tag color="gold" style={{ marginTop: 4 }}>
                          美学评分: {appliedImage.aesthetic_score.score ? Number(appliedImage.aesthetic_score.score).toFixed(2) : '-'}
                        </Tag>
                      )}
                      {/* 喜欢/不喜欢按钮 */}
                      <div style={{ marginTop: 12, display: 'flex', gap: 8, justifyContent: 'center' }}>
                        {preferences[appliedImage.id] === true ? (
                          <Button
                            type="primary"
                            icon={<LikeOutlined />}
                            size="small"
                            onClick={() => handleRemovePreference(appliedImage.id)}
                          >
                            已喜欢
                          </Button>
                        ) : preferences[appliedImage.id] === false ? (
                          <Button
                            danger
                            icon={<DislikeOutlined />}
                            size="small"
                            onClick={() => handleRemovePreference(appliedImage.id)}
                          >
                            已不喜欢
                          </Button>
                        ) : (
                          <>
                            <Button
                              type="text"
                              icon={<LikeOutlined />}
                              size="small"
                              onClick={() => handlePreference(appliedImage.id, true)}
                            >
                              喜欢
                            </Button>
                            <Button
                              type="text"
                              danger
                              icon={<DislikeOutlined />}
                              size="small"
                              onClick={() => handlePreference(appliedImage.id, false)}
                            >
                              不喜欢
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>

            {sortedImages.length === 0 && !loading && (
              <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                暂无LUT应用结果
              </div>
            )}
          </Spin>
        </Space>
      </Card>
    </div>
  )
}

export default SampleImageLutResults

