import React, { useState, useEffect } from 'react'
import {
  Card,
  Upload,
  Button,
  Space,
  message,
  Tag,
  Descriptions,
  Image,
  Spin,
  Typography,
  Select,
  InputNumber,
  Table,
  Progress,
  Row,
  Col,
  Divider,
  Modal,
  Drawer,
  Switch
} from 'antd'
import { UploadOutlined, SearchOutlined, ReloadOutlined, EyeOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Title, Text } = Typography
const { Option } = Select

const StyleMatch = () => {
  const [fileList, setFileList] = useState([])
  const [loading, setLoading] = useState(false)
  const [imageUrl, setImageUrl] = useState('')
  const [styles, setStyles] = useState([])
  const [selectedStyleIds, setSelectedStyleIds] = useState([])
  const [taggingResults, setTaggingResults] = useState({})
  const [featureWeights, setFeatureWeights] = useState({})
  const [matchResults, setMatchResults] = useState([])
  const [loadingMatch, setLoadingMatch] = useState(false)
  const [featuresMap, setFeaturesMap] = useState({}) // 存储特征信息 {featureId: {id, name, category}}
  const [compareVisible, setCompareVisible] = useState(false)
  const [compareData, setCompareData] = useState(null) // {originalImage, matchedImages: [], styleName}
  const [useAestheticScore, setUseAestheticScore] = useState(false) // 是否使用美学评分
  const [aestheticWeight, setAestheticWeight] = useState(0.4) // 美学评分权重（0-1）
  const [originalAestheticScore, setOriginalAestheticScore] = useState(null) // 原图的美学评分

  // 获取风格列表
  const fetchStyles = async () => {
    try {
      const response = await api.get('/styles', { params: { page: 1, page_size: 1000, status: 'active' } })
      if (response.code === 200) {
        setStyles(response.data.list || [])
      }
    } catch (error) {
      console.error('获取风格列表失败:', error)
      message.error('获取风格列表失败')
    }
  }

  // 获取特征列表
  const fetchFeatures = async () => {
    try {
      const response = await api.get('/features', { params: { page: 1, page_size: 1000, status: 'active' } })
      if (response.code === 200) {
        const features = response.data.list || []
        const map = {}
        features.forEach(feature => {
          map[feature.id] = {
            id: feature.id,
            name: feature.name,
            category: feature.category
          }
        })
        setFeaturesMap(map)
      }
    } catch (error) {
      console.error('获取特征列表失败:', error)
    }
  }

  useEffect(() => {
    fetchStyles()
    fetchFeatures()
  }, [])

  // 上传配置
  const uploadProps = {
    beforeUpload: (file) => {
      const isImage = file.type.startsWith('image/')
      if (!isImage) {
        message.error('只能上传图片文件！')
        return false
      }
      
      const isLt10M = file.size / 1024 / 1024 < 10
      if (!isLt10M) {
        message.error('图片大小不能超过10MB！')
        return false
      }
      
      const reader = new FileReader()
      reader.onload = (e) => {
        setImageUrl(e.target && e.target.result ? e.target.result : '')
      }
      reader.readAsDataURL(file)
      
      setFileList([file])
      setTaggingResults({})
      setMatchResults([])
      return false
    },
    fileList,
    onRemove: () => {
      setFileList([])
      setImageUrl('')
      setTaggingResults({})
      setMatchResults([])
      setSelectedStyleIds([])
      setFeatureWeights({})
      setOriginalAestheticScore(null)
    },
    maxCount: 1
  }

  // 分析图片特征
  const handleAnalyze = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择图片文件')
      return
    }

    setLoading(true)
    try {
      const file = fileList[0].originFileObj || fileList[0]
      const formData = new FormData()
      formData.append('file', file)

      const response = await api.post('/style-match/upload-and-analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      if (response.code === 200) {
        setTaggingResults(response.data.tagging_results || {})
        // 保存原图的美学评分
        if (response.data.aesthetic_score !== null && response.data.aesthetic_score !== undefined) {
          setOriginalAestheticScore(response.data.aesthetic_score)
        } else {
          setOriginalAestheticScore(null)
        }
        message.success('图片分析成功')
      } else {
        message.error(response.message || '分析失败')
      }
    } catch (error) {
      message.error('分析失败：' + (error.response?.data?.message || error.message))
      console.error('分析错误:', error)
    } finally {
      setLoading(false)
    }
  }

  // 选择风格后，获取特征并设置默认权重
  useEffect(() => {
    if (selectedStyleIds.length > 0 && Object.keys(taggingResults).length > 0) {
      fetchStyleFeatures()
    }
  }, [selectedStyleIds, taggingResults])

  // 获取选中风格的特征
  const fetchStyleFeatures = async () => {
    const allFeatureIds = new Set()
    const weights = { ...featureWeights } // 保留已有的权重设置

    for (const styleId of selectedStyleIds) {
      try {
        const response = await api.get(`/styles/${styleId}/feature-profiles`)
        if (response.code === 200) {
          const profiles = response.data || []
          for (const profile of profiles) {
            if (profile.is_selected) {
              allFeatureIds.add(profile.feature_id)
              // 如果该特征还没有设置权重，默认设置为1
              if (!weights[profile.feature_id]) {
                weights[profile.feature_id] = 1.0
              }
            }
          }
        }
      } catch (error) {
        console.error(`获取风格 ${styleId} 的特征失败:`, error)
      }
    }

    // 只更新新增的特征权重，保留已有的权重设置
    setFeatureWeights(prevWeights => {
      const newWeights = { ...prevWeights }
      // 只为新特征设置默认权重，已有权重的保持不变
      for (const featureId of allFeatureIds) {
        if (!newWeights[featureId]) {
          newWeights[featureId] = 1.0
        }
      }
      return newWeights
    })
    
    // 确保特征信息已加载
    if (Object.keys(featuresMap).length === 0) {
      await fetchFeatures()
    }
  }

  // 计算匹配度
  const handleCalculateMatch = async () => {
    if (selectedStyleIds.length === 0) {
      message.warning('请至少选择一个风格')
      return
    }

    if (Object.keys(taggingResults).length === 0) {
      message.warning('请先分析图片特征')
      return
    }

    setLoadingMatch(true)
    try {
      const response = await api.post('/style-match/calculate-match', {
        tagging_results: taggingResults,
        style_ids: selectedStyleIds,
        feature_weights: featureWeights,
        use_aesthetic_score: useAestheticScore,
        aesthetic_weight: aestheticWeight,
        original_aesthetic_score: originalAestheticScore
      })

      if (response.code === 200) {
        setMatchResults(response.data.results || [])
        message.success('匹配度计算完成')
      } else {
        message.error(response.message || '计算失败')
      }
    } catch (error) {
      message.error('计算失败：' + (error.response?.data?.message || error.message))
      console.error('计算错误:', error)
    } finally {
      setLoadingMatch(false)
    }
  }

  // 获取特征名称
  const getFeatureName = async (featureId) => {
    try {
      const response = await api.get(`/features/${featureId}`)
      if (response.code === 200) {
        return response.data.name
      }
    } catch (error) {
      console.error('获取特征名称失败:', error)
    }
    return `特征 ${featureId}`
  }

  // 匹配结果表格列
  const matchColumns = [
    {
      title: '排名',
      key: 'rank',
      width: 80,
      render: (_, __, index) => index + 1
    },
    {
      title: '风格名称',
      dataIndex: 'style_name',
      key: 'style_name',
      width: 200
    },
    {
      title: '匹配分数',
      key: 'match_score',
      width: 200,
      render: (_, record) => {
        const matchScore = record.match_score || 0  // 归一化后的值（0-1之间）
        const totalMatchScore = record.total_match_score || 0
        // match_score是归一化后的值（0-1），需要乘以100来显示百分比
        const percentValue = matchScore * 100
        const normalizedPercent = Math.max(0, Math.min(100, percentValue))
        return (
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Space>
              <Progress 
                type="circle" 
                percent={normalizedPercent} 
                size={60}
                format={(percent) => `${percent.toFixed(1)}`}
                strokeColor={{
                  '0%': '#ff4d4f',
                  '50%': '#faad14',
                  '100%': '#52c41a',
                }}
              />
              <Space direction="vertical" size={0}>
                <div style={{ fontSize: 16, fontWeight: 'bold' }}>
                  match_score: {(matchScore * 100).toFixed(2)}%
                </div>
                <div style={{ fontSize: 14, color: '#666' }}>
                  total_match_score: {totalMatchScore.toFixed(2)}
                </div>
              </Space>
            </Space>
          </Space>
        )
      }
    },
    {
      title: '匹配度最高的三个特征',
      key: 'top_features',
      width: 300,
      render: (_, record) => (
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          {record.top_features && record.top_features.length > 0 ? (
            record.top_features.map((feature, idx) => (
              <Tag key={idx} color="blue">
                {feature.feature_name}: {feature.feature_value} 
                ({feature.matched_percentage}%, 得分: {feature.match_score})
              </Tag>
            ))
          ) : (
            <span style={{ color: '#999' }}>无匹配特征</span>
          )}
        </Space>
      )
    },
    {
      title: '匹配度最高的三张图片',
      key: 'top_images',
      width: 400,
      render: (_, record) => {
        const getImageUrl = (image) => {
          if (image && image.storage_path) {
            return `/api/images/file/${image.id}/content`
          }
          return null
        }
        
        return (
          <Row gutter={[8, 8]}>
            {record.top_images && record.top_images.length > 0 ? (
              record.top_images.map((item, idx) => {
                const imageUrl = getImageUrl(item.image)
                return (
                  <Col key={idx} span={8}>
                    <div style={{ position: 'relative' }}>
                      {imageUrl ? (
                        <Image
                          src={imageUrl}
                          alt={`图片 ${item.image_id}`}
                          style={{ 
                            width: '100%', 
                            height: 100, 
                            objectFit: 'cover',
                            borderRadius: 4
                          }}
                          preview={{
                            mask: '预览'
                          }}
                        />
                      ) : (
                        <div style={{ 
                          width: '100%', 
                          height: 100, 
                          backgroundColor: '#f5f5f5',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          borderRadius: 4,
                          color: '#999',
                          fontSize: 12
                        }}>
                          无图片
                        </div>
                      )}
                      <div style={{ 
                        position: 'absolute', 
                        bottom: 0, 
                        left: 0, 
                        right: 0,
                        background: 'rgba(0,0,0,0.6)',
                        color: '#fff',
                        fontSize: 10,
                        padding: '2px 4px',
                        textAlign: 'center',
                        borderRadius: '0 0 4px 4px'
                      }}>
                        匹配度: {(item.match_score * 100).toFixed(2)}%
                      </div>
                    </div>
                  </Col>
                )
              })
            ) : (
              <Col span={24}>
                <span style={{ color: '#999' }}>无匹配图片</span>
              </Col>
            )}
          </Row>
        )
      }
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      fixed: 'right',
      render: (_, record) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => {
            setCompareData({
              originalImage: imageUrl,
              matchedImages: record.top_images || [],
              styleName: record.style_name
            })
            setCompareVisible(true)
          }}
        >
          对比
        </Button>
      )
    }
  ]

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Title level={4}>风格匹配</Title>
        
        <Row gutter={[24, 24]}>
          {/* 左侧：图片上传和分析 */}
          <Col xs={24} lg={12}>
            <Card title="图片上传" style={{ marginBottom: 16 }}>
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                <Upload {...uploadProps}>
                  <Button icon={<UploadOutlined />}>选择图片</Button>
                </Upload>
                
                {imageUrl && (
                  <div style={{ textAlign: 'center' }}>
                    <Image
                      src={imageUrl}
                      alt="预览"
                      style={{ maxWidth: '100%', maxHeight: 300 }}
                      preview={false}
                    />
                  </div>
                )}
                
                <Button
                  type="primary"
                  icon={<SearchOutlined />}
                  onClick={handleAnalyze}
                  loading={loading}
                  disabled={fileList.length === 0}
                >
                  分析图片特征
                </Button>
                
                {Object.keys(taggingResults).length > 0 && (
                  <Card size="small" title="分析结果">
                    <Descriptions column={1} size="small">
                      {Object.entries(taggingResults).map(([featureId, value]) => {
                        const feature = featuresMap[featureId] || {}
                        const label = feature.name 
                          ? `${feature.name}${feature.category ? ` (${feature.category})` : ''} [ID: ${featureId}]`
                          : `特征 ${featureId}`
                        return (
                          <Descriptions.Item key={featureId} label={label}>
                            {value}
                          </Descriptions.Item>
                        )
                      })}
                    </Descriptions>
                  </Card>
                )}
              </Space>
            </Card>
          </Col>

          {/* 右侧：风格选择和权重设置 */}
          <Col xs={24} lg={12}>
            <Card title="风格选择" style={{ marginBottom: 16 }}>
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                <Select
                  mode="multiple"
                  placeholder="选择要匹配的风格"
                  style={{ width: '100%' }}
                  value={selectedStyleIds}
                  onChange={setSelectedStyleIds}
                  disabled={Object.keys(taggingResults).length === 0}
                >
                  {styles.map(style => (
                    <Option key={style.id} value={style.id}>
                      {style.name}
                    </Option>
                  ))}
                </Select>

                {selectedStyleIds.length > 0 && Object.keys(featureWeights).length > 0 && (
                  <Card size="small" title="特征权重设置">
                    <Space direction="vertical" style={{ width: '100%' }} size="middle">
                      {Object.entries(featureWeights).map(([featureId, weight]) => {
                        const feature = featuresMap[featureId] || {}
                        const label = feature.name 
                          ? `${feature.name}${feature.category ? ` (${feature.category})` : ''} [ID: ${featureId}]`
                          : `特征 ${featureId}`
                        return (
                          <div key={featureId} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ minWidth: 200, fontSize: 12 }}>{label}:</span>
                            <InputNumber
                              min={0}
                              max={10}
                              step={0.1}
                              value={weight}
                              onChange={(value) => {
                                setFeatureWeights({
                                  ...featureWeights,
                                  [featureId]: value !== null && value !== undefined ? value : 0
                                })
                              }}
                              style={{ flex: 1 }}
                            />
                          </div>
                        )
                      })}
                    </Space>
                  </Card>
                )}

                {/* 美学评分设置 */}
                <Card size="small" title="美学评分设置">
                  <Space direction="vertical" style={{ width: '100%' }} size="middle">
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span>使用美学评分</span>
                      <Switch
                        checked={useAestheticScore}
                        onChange={setUseAestheticScore}
                      />
                    </div>
                    {useAestheticScore && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ minWidth: 100, fontSize: 12 }}>美学评分权重:</span>
                        <InputNumber
                          min={0}
                          max={1}
                          step={0.01}
                          precision={2}
                          value={aestheticWeight}
                          onChange={(value) => {
                            setAestheticWeight(value !== null && value !== undefined ? value : 0)
                          }}
                          style={{ flex: 1 }}
                        />
                        <span style={{ fontSize: 12, color: '#999' }}>范围: 0-1</span>
                      </div>
                    )}
                  </Space>
                </Card>

                <Button
                  type="primary"
                  icon={<SearchOutlined />}
                  onClick={handleCalculateMatch}
                  loading={loadingMatch}
                  disabled={selectedStyleIds.length === 0 || Object.keys(taggingResults).length === 0}
                  block
                >
                  计算匹配度
                </Button>
              </Space>
            </Card>
          </Col>
        </Row>

        {/* 匹配结果 */}
        {matchResults.length > 0 && (
          <Card title="匹配结果" style={{ marginTop: 24 }}>
            <Table
              columns={matchColumns}
              dataSource={matchResults}
              rowKey="style_id"
              pagination={false}
            />
          </Card>
        )}
      </Card>

        {/* 图片对比抽屉 */}
        <Drawer
          title={`图片对比 - ${compareData?.styleName || ''}`}
          open={compareVisible}
          onClose={() => setCompareVisible(false)}
          width={1200}
          placement="right"
        >
          {compareData && (
            <div>
              <Row gutter={[16, 16]}>
                {/* 原图 */}
                <Col span={24}>
                  <Card title="原图" size="small">
                    <div style={{ textAlign: 'center' }}>
                      <Image
                        src={compareData.originalImage}
                        alt="原图"
                        style={{ maxWidth: '100%', maxHeight: 400 }}
                        preview={{
                          mask: '预览'
                        }}
                      />
                    </div>
                  </Card>
                </Col>
                
                {/* 匹配的图片 */}
                <Col span={24}>
                  <Card title={`匹配的图片（共 ${compareData.matchedImages.length} 张）`} size="small">
                    <Row gutter={[16, 16]}>
                      {compareData.matchedImages.map((item, idx) => {
                        const getImageUrl = (image) => {
                          if (image && image.storage_path) {
                            return `/api/images/file/${image.id}/content`
                          }
                          return null
                        }
                        const imageUrl = getImageUrl(item.image)
                        return (
                          <Col key={idx} span={8}>
                            <Card
                              size="small"
                              title={`图片 ${idx + 1}`}
                              extra={
                                <Tag color="blue">
                                  匹配度: {(item.match_score * 100).toFixed(2)}%
                                </Tag>
                              }
                            >
                              {imageUrl ? (
                                <Image
                                  src={imageUrl}
                                  alt={`匹配图片 ${idx + 1}`}
                                  style={{ 
                                    width: '100%',
                                    maxHeight: 300,
                                    objectFit: 'contain'
                                  }}
                                  preview={{
                                    mask: '预览'
                                  }}
                                />
                              ) : (
                                <div style={{ 
                                  width: '100%', 
                                  height: 200, 
                                  backgroundColor: '#f5f5f5',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  color: '#999',
                                  fontSize: 12
                                }}>
                                  无图片
                                </div>
                              )}
                            </Card>
                          </Col>
                        )
                      })}
                    </Row>
                  </Card>
                </Col>
              </Row>
            </div>
          )}
        </Drawer>
    </div>
  )
}

export default StyleMatch

