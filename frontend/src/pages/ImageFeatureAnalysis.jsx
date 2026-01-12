import React, { useState, useEffect } from 'react'
import { Card, Checkbox, Row, Col, Spin, message, Empty, Modal, Button, Select } from 'antd'
import { FullscreenOutlined } from '@ant-design/icons'
import { Column } from '@ant-design/plots'
import api from '../services/api'

const { Option } = Select

const ImageFeatureAnalysis = () => {
  const [features, setFeatures] = useState([])
  const [selectedFeatureIds, setSelectedFeatureIds] = useState([])
  const [featureStats, setFeatureStats] = useState({})
  const [summaryData, setSummaryData] = useState([])
  const [loading, setLoading] = useState(false)
  const [featuresLoading, setFeaturesLoading] = useState(false)
  const [fullscreenVisible, setFullscreenVisible] = useState(false)
  const [featureGroups, setFeatureGroups] = useState([])
  const [selectedFeatureGroupId, setSelectedFeatureGroupId] = useState(null)

  // 获取特征列表和特征组列表
  useEffect(() => {
    fetchFeatures()
    fetchFeatureGroups()
  }, [])

  // 当选择的特征变化时，获取统计数据
  useEffect(() => {
    if (selectedFeatureIds.length > 0) {
      fetchFeatureStats()
    } else {
      setFeatureStats({})
      setSummaryData([])
    }
  }, [selectedFeatureIds])

  const fetchFeatures = async () => {
    setFeaturesLoading(true)
    try {
      const response = await api.get('/statistics/features')
      if (response.code === 200) {
        setFeatures(response.data || [])
      } else {
        message.error(response.message || '获取特征列表失败')
      }
    } catch (error) {
      message.error('获取特征列表失败：' + (error.response?.data?.message || error.message))
    } finally {
      setFeaturesLoading(false)
    }
  }

  const fetchFeatureStats = async () => {
    setLoading(true)
    try {
      const response = await api.post('/statistics/feature-stats', {
        feature_ids: selectedFeatureIds
      })
      if (response.code === 200) {
        setFeatureStats(response.data.feature_stats || {})
        setSummaryData(response.data.summary || [])
      } else {
        message.error(response.message || '获取特征统计失败')
      }
    } catch (error) {
      message.error('获取特征统计失败：' + (error.response?.data?.message || error.message))
    } finally {
      setLoading(false)
    }
  }

  const fetchFeatureGroups = async () => {
    try {
      const response = await api.get('/feature-groups/all')
      if (response.code === 200) {
        setFeatureGroups(response.data || [])
      } else {
        message.error(response.message || '获取特征组列表失败')
      }
    } catch (error) {
      message.error('获取特征组列表失败：' + (error.response?.data?.message || error.message))
    }
  }

  const handleFeatureGroupChange = async (groupId) => {
    setSelectedFeatureGroupId(groupId)
    
    if (!groupId) {
      // 如果取消选择特征组，不清空已选择的特征
      return
    }
    
    try {
      // 获取特征组详情，包含该组下的所有特征
      const response = await api.get(`/feature-groups/${groupId}`)
      if (response.code === 200) {
        const group = response.data
        const groupFeatureIds = (group.features || [])
          .filter(f => f.enabled !== false && f.status !== 'inactive') // 只选择启用的特征
          .map(f => f.id)
        
        if (groupFeatureIds.length > 0) {
          // 合并已选择的特征ID和新选择的特征ID，去重
          const newSelectedIds = [...new Set([...selectedFeatureIds, ...groupFeatureIds])]
          setSelectedFeatureIds(newSelectedIds)
          message.success(`已选择特征组"${group.name}"下的 ${groupFeatureIds.length} 个特征`)
        } else {
          message.warning(`特征组"${group.name}"下没有启用的特征`)
        }
      } else {
        message.error(response.message || '获取特征组详情失败')
      }
    } catch (error) {
      message.error('获取特征组详情失败：' + (error.response?.data?.message || error.message))
    }
  }

  const handleFeatureChange = (checkedValues) => {
    setSelectedFeatureIds(checkedValues)
    // 如果手动取消了一些特征，可能需要清除特征组选择
    // 这里保持特征组选择，允许用户手动调整
  }

  // 渲染单个特征的柱状图
  const renderFeatureChart = (featureId, featureStat) => {
    if (!featureStat || !featureStat.values || featureStat.values.length === 0) {
      return (
        <Card title={featureStat.feature_name} size="small">
          <Empty description="暂无数据" />
        </Card>
      )
    }

    // 将Ant Design的颜色名称转换为十六进制颜色值
    const colorMap = {
      'blue': '#1890ff',
      'green': '#52c41a',
      'red': '#ff4d4f',
      'orange': '#fa8c16',
      'purple': '#722ed1',
      'cyan': '#13c2c2',
      'magenta': '#eb2f96',
      'gold': '#faad14',
      'lime': '#a0d911',
      'geekblue': '#2f54eb',
      'volcano': '#fa541c'
    }
    
    // 获取特征颜色：优先使用featureStat中的颜色，如果没有则从features列表中查找
    let featureColor = featureStat.feature_color
    if (!featureColor) {
      const feature = features.find(f => f.id === featureId)
      featureColor = feature?.color || 'blue'
    }
    const hexColor = colorMap[featureColor] || colorMap['blue']
    
    // 调试：打印特征颜色信息
    console.log(`特征 ${featureStat.feature_name} (ID: ${featureId}) 的颜色:`, {
      featureStat_color: featureStat.feature_color,
      feature_color: features.find(f => f.id === featureId)?.color,
      finalColor: featureColor,
      hexColor
    })

    // 在数据中添加颜色字段
    const chartData = featureStat.values.map(item => ({
      value: item.value,
      count: item.count,
      color: hexColor  // 在数据项中指定颜色
    }))

    const config = {
      data: chartData,
      xField: 'value',
      yField: 'count',
      columnWidthRatio: 0.6,
      columnStyle: (datum) => {
        // 根据数据项中的color字段设置颜色
        return {
          fill: datum.color || hexColor
        }
      },
      label: {
        position: 'top',
        style: {
          fill: '#666',
          fontSize: 12
        }
      },
      xAxis: {
        label: {
          autoRotate: false,
          autoHide: true
        }
      },
      meta: {
        value: {
          alias: '特征值'
        },
        count: {
          alias: '图片数'
        }
      }
    }

    return (
      <Card title={featureStat.feature_name} size="small" style={{ marginBottom: 16 }}>
        <Column {...config} height={300} />
      </Card>
    )
  }

  // 渲染汇总柱状图
  const renderSummaryChart = () => {
    if (summaryData.length === 0) {
      return (
        <Card title="汇总统计" size="small">
          <Empty description="请先选择特征" />
        </Card>
      )
    }

    // 颜色映射：将Ant Design的颜色名称转换为十六进制颜色值
    const colorMap = {
      'blue': '#1890ff',
      'green': '#52c41a',
      'red': '#ff4d4f',
      'orange': '#fa8c16',
      'purple': '#722ed1',
      'cyan': '#13c2c2',
      'magenta': '#eb2f96',
      'gold': '#faad14',
      'lime': '#a0d911',
      'geekblue': '#2f54eb',
      'volcano': '#fa541c'
    }

    // 构建图表数据：特征名_特征值作为横坐标，并包含颜色信息
    const chartData = summaryData.map(item => {
      const featureColor = item.feature_color || 'blue'
      const hexColor = colorMap[featureColor] || colorMap['blue']
      return {
        label: `${item.feature_name}: ${item.value}`,
        count: item.count,
        featureColor: featureColor,
        color: hexColor  // 直接添加十六进制颜色值
      }
    })

    const config = {
      data: chartData,
      xField: 'label',
      yField: 'count',
      columnWidthRatio: 0.6,
      columnStyle: (datum) => {
        // 根据数据项中的color字段设置颜色
        return {
          fill: datum.color || colorMap['blue']
        }
      },
      label: {
        position: 'top',
        style: {
          fill: '#666',
          fontSize: 12
        }
      },
      xAxis: {
        label: {
          autoRotate: true,
          autoHide: true,
          style: {
            fontSize: 10
          }
        }
      },
      meta: {
        label: {
          alias: '特征值'
        },
        count: {
          alias: '图片数'
        }
      }
    }

    return (
      <Card 
        title="汇总统计" 
        size="small"
        extra={
          <Button
            type="text"
            icon={<FullscreenOutlined />}
            onClick={() => setFullscreenVisible(true)}
            title="全屏查看"
          />
        }
      >
        <Column {...config} height={400} />
      </Card>
    )
  }

  // 渲染全屏汇总图表
  const renderFullscreenChart = () => {
    if (summaryData.length === 0) {
      return null
    }

    // 颜色映射：将Ant Design的颜色名称转换为十六进制颜色值
    const colorMap = {
      'blue': '#1890ff',
      'green': '#52c41a',
      'red': '#ff4d4f',
      'orange': '#fa8c16',
      'purple': '#722ed1',
      'cyan': '#13c2c2',
      'magenta': '#eb2f96',
      'gold': '#faad14',
      'lime': '#a0d911',
      'geekblue': '#2f54eb',
      'volcano': '#fa541c'
    }

    // 构建图表数据：特征名_特征值作为横坐标，并包含颜色信息
    const chartData = summaryData.map(item => {
      const featureColor = item.feature_color || 'blue'
      const hexColor = colorMap[featureColor] || colorMap['blue']
      return {
        label: `${item.feature_name}: ${item.value}`,
        count: item.count,
        featureColor: featureColor,
        color: hexColor
      }
    })

    const config = {
      data: chartData,
      xField: 'label',
      yField: 'count',
      columnWidthRatio: 0.6,
      columnStyle: (datum) => {
        // 根据数据项中的color字段设置颜色
        return {
          fill: datum.color || colorMap['blue']
        }
      },
      label: {
        position: 'top',
        style: {
          fill: '#666',
          fontSize: 14
        }
      },
      xAxis: {
        label: {
          autoRotate: true,
          autoHide: true,
          style: {
            fontSize: 12
          }
        }
      },
      meta: {
        label: {
          alias: '特征值'
        },
        count: {
          alias: '图片数'
        }
      }
    }

    // 计算全屏高度（视口高度减去Modal的padding）
    const fullscreenHeight = window.innerHeight - 120

    return <Column {...config} height={fullscreenHeight} />
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card title="图片库特征分析" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          {/* 第一部分：特征选择区 */}
          <Col span={24}>
            <Card title="特征选择" size="small" style={{ marginBottom: 16 }}>
              <Spin spinning={featuresLoading}>
                {/* 特征组快速选择 */}
                <div style={{ marginBottom: 16 }}>
                  <Select
                    placeholder="选择特征组快速选择特征"
                    style={{ width: 300 }}
                    allowClear
                    value={selectedFeatureGroupId}
                    onChange={handleFeatureGroupChange}
                  >
                    {featureGroups.map(group => (
                      <Option key={group.id} value={group.id}>
                        {group.name}
                        {group.description && <span style={{ color: '#999', fontSize: '12px' }}> - {group.description}</span>}
                      </Option>
                    ))}
                  </Select>
                </div>
                
                <Checkbox.Group
                  style={{ width: '100%' }}
                  value={selectedFeatureIds}
                  onChange={handleFeatureChange}
                >
                  <Row gutter={[16, 16]}>
                    {features.map(feature => (
                      <Col key={feature.id} span={6}>
                        <Checkbox value={feature.id}>
                          {feature.name}
                          {feature.category && <span style={{ color: '#999', fontSize: '12px' }}> ({feature.category})</span>}
                        </Checkbox>
                      </Col>
                    ))}
                  </Row>
                </Checkbox.Group>
              </Spin>
            </Card>
          </Col>
        </Row>

        <Spin spinning={loading}>
          {/* 第二部分：特征统计区 */}
          {selectedFeatureIds.length > 0 && (
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={24}>
                <Card title="特征统计" size="small">
                  {selectedFeatureIds.length === 0 ? (
                    <Empty description="请先选择特征" />
                  ) : (
                    <Row gutter={16}>
                      {selectedFeatureIds.map(featureId => {
                        const featureStat = featureStats[featureId]
                        if (!featureStat) {
                          return (
                            <Col key={featureId} span={12}>
                              <Card title="加载中..." size="small">
                                <Spin />
                              </Card>
                            </Col>
                          )
                        }
                        return (
                          <Col key={featureId} span={12}>
                            {renderFeatureChart(featureId, featureStat)}
                          </Col>
                        )
                      })}
                    </Row>
                  )}
                </Card>
              </Col>
            </Row>
          )}

          {/* 第三部分：汇总柱状图 */}
          <Row gutter={16}>
            <Col span={24}>
              {renderSummaryChart()}
            </Col>
          </Row>
        </Spin>
      </Card>

      {/* 全屏查看汇总统计Modal */}
      <Modal
        title="汇总统计 - 全屏查看"
        open={fullscreenVisible}
        onCancel={() => setFullscreenVisible(false)}
        footer={null}
        width="100%"
        style={{ top: 0, paddingBottom: 0 }}
        bodyStyle={{ padding: '24px', height: 'calc(100vh - 55px)' }}
        destroyOnClose
      >
        {renderFullscreenChart()}
      </Modal>
    </div>
  )
}

export default ImageFeatureAnalysis
