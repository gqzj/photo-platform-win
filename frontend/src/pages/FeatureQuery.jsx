import React, { useState, useEffect } from 'react'
import {
  Card,
  Button,
  Space,
  Input,
  message,
  Tag,
  Row,
  Col,
  Image,
  Select,
  Empty,
  Pagination,
  Spin
} from 'antd'
import {
  SearchOutlined,
  PlusOutlined,
  DeleteOutlined
} from '@ant-design/icons'
import api from '../services/api'

const { Option } = Select

// 获取图片URL的工具函数
const getImageUrl = (image) => {
  if (image.storage_path) {
    return `/api/images/file/${image.id}/content`
  }
  if (image.original_url) {
    return image.original_url
  }
  return `/api/images/file/${image.id}/content`
}

const FeatureQuery = () => {
  const [features, setFeatures] = useState([]) // 特征列表（只包含启用的）
  const [selectedFeatures, setSelectedFeatures] = useState([]) // 选中的特征和特征值
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  })

  // 获取特征列表（只获取启用的）
  const fetchFeatures = async () => {
    try {
      const response = await api.get('/features', {
        params: {
          page: 1,
          page_size: 1000, // 获取所有特征
          status: 'active' // 只获取启用的特征
        }
      })
      if (response.code === 200) {
        // 过滤掉禁用的特征
        const enabledFeatures = response.data.list.filter(f => f.enabled !== false && f.status !== 'inactive')
        setFeatures(enabledFeatures)
      }
    } catch (error) {
      console.error('获取特征列表失败:', error)
      message.error('获取特征列表失败')
    }
  }

  useEffect(() => {
    fetchFeatures()
  }, [])

  // 添加特征
  const handleAddFeature = () => {
    setSelectedFeatures([...selectedFeatures, { feature_id: null, feature_name: '', values: [] }])
  }

  // 删除特征
  const handleRemoveFeature = (index) => {
    const newFeatures = selectedFeatures.filter((_, i) => i !== index)
    setSelectedFeatures(newFeatures)
  }

  // 更新特征选择
  const handleFeatureChange = (index, featureId) => {
    const newFeatures = [...selectedFeatures]
    const feature = features.find(f => f.id === featureId)
    if (feature) {
      newFeatures[index].feature_id = featureId
      newFeatures[index].feature_name = feature.name
      // 从特征的values_json中获取特征值
      let featureValues = []
      if (feature.values_json) {
        try {
          const valuesData = typeof feature.values_json === 'string' 
            ? JSON.parse(feature.values_json) 
            : feature.values_json
          if (Array.isArray(valuesData)) {
            featureValues = valuesData
          } else if (typeof valuesData === 'object' && valuesData !== null) {
            featureValues = Object.values(valuesData)
          }
        } catch (e) {
          console.error('解析特征值失败:', e)
        }
      }
      newFeatures[index].values = featureValues
      newFeatures[index].selectedValues = [] // 重置选中的值
    }
    setSelectedFeatures(newFeatures)
  }

  // 更新特征值选择
  const handleFeatureValuesChange = (index, selectedValues) => {
    const newFeatures = [...selectedFeatures]
    newFeatures[index].selectedValues = selectedValues || []
    setSelectedFeatures(newFeatures)
  }

  // 查询图片
  const handleSearch = async (page = 1) => {
    // 验证
    if (selectedFeatures.length === 0) {
      message.warning('请至少选择一个特征')
      return
    }

    for (let i = 0; i < selectedFeatures.length; i++) {
      const feature = selectedFeatures[i]
      if (!feature.feature_id) {
        message.warning(`第 ${i + 1} 个特征请选择特征`)
        return
      }
      if (!feature.selectedValues || feature.selectedValues.length === 0) {
        message.warning(`第 ${i + 1} 个特征至少需要选择一个特征值`)
        return
      }
    }

    setLoading(true)
    try {
      const requestData = {
        features: selectedFeatures.map(f => ({
          feature_id: f.feature_id,
          values: f.selectedValues
        })),
        page: page,
        page_size: pagination.pageSize
      }

      const response = await api.post('/feature-query/search', requestData)
      if (response.code === 200) {
        setResults(response.data.list || [])
        setPagination({
          ...pagination,
          current: response.data.page,
          total: response.data.total
        })
        message.success(`找到 ${response.data.total} 张图片`)
      } else {
        message.error(response.message || '查询失败')
        setResults([])
      }
    } catch (error) {
      message.error('查询失败：' + (error.response?.data?.message || error.message))
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card title="特征组合查询" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 特征选择区域 */}
          <div>
            <div style={{ marginBottom: 16 }}>
              <Button type="dashed" onClick={handleAddFeature} icon={<PlusOutlined />}>
                添加特征
              </Button>
            </div>

            {selectedFeatures.map((feature, index) => {
              const selectedFeature = features.find(f => f.id === feature.feature_id)
              // 获取特征值列表
              let featureValues = []
              if (selectedFeature && selectedFeature.values_json) {
                try {
                  const valuesData = typeof selectedFeature.values_json === 'string' 
                    ? JSON.parse(selectedFeature.values_json) 
                    : selectedFeature.values_json
                  if (Array.isArray(valuesData)) {
                    featureValues = valuesData
                  } else if (typeof valuesData === 'object' && valuesData !== null) {
                    featureValues = Object.values(valuesData)
                  }
                } catch (e) {
                  console.error('解析特征值失败:', e)
                }
              }

              return (
                <Card key={index} size="small" style={{ marginBottom: 16 }} title={`特征 ${index + 1}`} extra={
                  <Button type="link" danger size="small" onClick={() => handleRemoveFeature(index)} icon={<DeleteOutlined />}>
                    删除
                  </Button>
                }>
                  <Row gutter={16}>
                    <Col span={12}>
                      <div style={{ marginBottom: 8 }}>选择特征：</div>
                      <Select
                        placeholder="请选择特征"
                        value={feature.feature_id}
                        onChange={(value) => handleFeatureChange(index, value)}
                        style={{ width: '100%' }}
                        showSearch
                        filterOption={(input, option) =>
                          (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                        }
                      >
                        {features.map(f => (
                          <Option key={f.id} value={f.id} label={f.name}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span>{f.name}</span>
                              {f.category && (
                                <Tag color="blue" style={{ marginLeft: 8, fontSize: 12 }}>
                                  {f.category}
                                </Tag>
                              )}
                            </div>
                          </Option>
                        ))}
                      </Select>
                    </Col>
                    <Col span={12}>
                      <div style={{ marginBottom: 8 }}>选择特征值（可多选）：</div>
                      <Select
                        mode="multiple"
                        placeholder={selectedFeature ? "请选择特征值" : "请先选择特征"}
                        value={feature.selectedValues || []}
                        onChange={(values) => handleFeatureValuesChange(index, values)}
                        style={{ width: '100%' }}
                        disabled={!selectedFeature || featureValues.length === 0}
                      >
                        {featureValues.map((value, idx) => (
                          <Option key={idx} value={value}>
                            {value}
                          </Option>
                        ))}
                      </Select>
                      {selectedFeature && featureValues.length === 0 && (
                        <div style={{ color: '#999', fontSize: 12, marginTop: 4 }}>
                          该特征没有定义特征值
                        </div>
                      )}
                    </Col>
                  </Row>
                </Card>
              )
            })}
          </div>

          {/* 查询按钮 */}
          <div>
            <Button
              type="primary"
              icon={<SearchOutlined />}
              onClick={() => handleSearch(1)}
              loading={loading}
              disabled={selectedFeatures.length === 0}
            >
              查询图片
            </Button>
          </div>
        </Space>
      </Card>

      {/* 查询结果 */}
      {results.length > 0 && (
        <Card title={`查询结果 (${pagination.total} 张)`}>
          <Spin spinning={loading}>
            <Row gutter={[16, 16]}>
              {results.map((image) => {
                const imageUrl = getImageUrl(image)
                return (
                  <Col key={image.id} xs={24} sm={12} md={8} lg={6} xl={4}>
                    <Card
                      hoverable
                      cover={
                        <div style={{
                          width: '100%',
                          aspectRatio: '1',
                          overflow: 'hidden',
                          backgroundColor: '#f5f5f5',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}>
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
                        </div>
                      }
                      bodyStyle={{ padding: 12 }}
                    >
                      <div style={{ fontSize: 12, color: '#666' }}>
                        ID: {image.id}
                      </div>
                      {image.filename && (
                        <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                          {image.filename.length > 20 ? image.filename.substring(0, 20) + '...' : image.filename}
                        </div>
                      )}
                    </Card>
                  </Col>
                )
              })}
            </Row>

            <div style={{ marginTop: 16, textAlign: 'right' }}>
              <Pagination
                current={pagination.current}
                pageSize={pagination.pageSize}
                total={pagination.total}
                showSizeChanger
                showTotal={(total) => `共 ${total} 张图片`}
                onChange={(page, pageSize) => {
                  setPagination({ ...pagination, current: page, pageSize })
                  handleSearch(page)
                }}
                onShowSizeChange={(current, size) => {
                  setPagination({ ...pagination, current: 1, pageSize: size })
                  handleSearch(1)
                }}
              />
            </div>
          </Spin>
        </Card>
      )}

      {results.length === 0 && !loading && selectedFeatures.length > 0 && (
        <Card>
          <Empty description="暂无查询结果，请点击查询按钮" />
        </Card>
      )}
    </div>
  )
}

export default FeatureQuery
