import React, { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Table, Select, Spin, message, Tag, Progress, Empty } from 'antd'
import { BarChartOutlined, PieChartOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Option } = Select

const FeatureAnalysis = () => {
  const [loading, setLoading] = useState(false)
  const [statistics, setStatistics] = useState(null)
  const [selectedFeatureId, setSelectedFeatureId] = useState(null)
  const [featureDistribution, setFeatureDistribution] = useState(null)
  const [loadingDistribution, setLoadingDistribution] = useState(false)

  // 获取统计数据
  useEffect(() => {
    fetchStatistics()
  }, [])

  // 获取特征值分布
  useEffect(() => {
    if (selectedFeatureId) {
      fetchFeatureDistribution(selectedFeatureId)
    } else {
      setFeatureDistribution(null)
    }
  }, [selectedFeatureId])

  const fetchStatistics = async () => {
    setLoading(true)
    try {
      const response = await api.get('/feature-analysis/statistics')
      if (response.code === 200) {
        setStatistics(response.data)
        // 默认选择第一个特征
        if (response.data.feature_statistics && response.data.feature_statistics.length > 0) {
          setSelectedFeatureId(response.data.feature_statistics[0].feature_id)
        }
      } else {
        message.error(response.message || '获取统计数据失败')
      }
    } catch (error) {
      message.error('获取统计数据失败：' + (error.response?.data?.message || error.message))
      console.error('获取统计数据错误:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchFeatureDistribution = async (featureId) => {
    setLoadingDistribution(true)
    try {
      const response = await api.get(`/feature-analysis/feature/${featureId}/distribution`)
      if (response.code === 200) {
        setFeatureDistribution(response.data)
      } else {
        message.error(response.message || '获取特征值分布失败')
      }
    } catch (error) {
      message.error('获取特征值分布失败：' + (error.response?.data?.message || error.message))
      console.error('获取特征值分布错误:', error)
    } finally {
      setLoadingDistribution(false)
    }
  }

  // 特征统计表格列
  const featureColumns = [
    {
      title: '特征名称',
      dataIndex: 'feature_name',
      key: 'feature_name',
      width: 200,
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{text}</div>
          {record.feature_category && (
            <div style={{ fontSize: 12, color: '#999' }}>{record.feature_category}</div>
          )}
        </div>
      )
    },
    {
      title: '打标图片数',
      dataIndex: 'tagged_image_count',
      key: 'tagged_image_count',
      width: 120,
      sorter: (a, b) => a.tagged_image_count - b.tagged_image_count,
      render: (count) => <Tag color="blue">{count}</Tag>
    },
    {
      title: '不同值数量',
      dataIndex: 'distinct_value_count',
      key: 'distinct_value_count',
      width: 120,
      sorter: (a, b) => a.distinct_value_count - b.distinct_value_count,
      render: (count) => <Tag color="green">{count}</Tag>
    },
    {
      title: '总记录数',
      dataIndex: 'total_records',
      key: 'total_records',
      width: 120,
      sorter: (a, b) => a.total_records - b.total_records
    }
  ]


  return (
    <div>
      <Spin spinning={loading}>
        {statistics && (
          <>
            {/* 总体统计 */}
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="特征总数"
                    value={statistics.total_features}
                    prefix={<BarChartOutlined />}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="已打标图片数"
                    value={statistics.total_tagged_images}
                    prefix={<PieChartOutlined />}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="打标记录总数"
                    value={statistics.total_tagging_records}
                    valueStyle={{ color: '#faad14' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="平均每张图片特征数"
                    value={
                      statistics.total_tagged_images > 0
                        ? (statistics.total_tagging_records / statistics.total_tagged_images).toFixed(2)
                        : 0
                    }
                    valueStyle={{ color: '#722ed1' }}
                  />
                </Card>
              </Col>
            </Row>

            {/* 特征统计表格 */}
            <Card
              title="特征统计列表"
              style={{ marginBottom: 24 }}
              extra={
                <Select
                  placeholder="选择特征查看详细分布"
                  style={{ width: 300 }}
                  value={selectedFeatureId}
                  onChange={setSelectedFeatureId}
                  showSearch
                  filterOption={(input, option) =>
                    option?.children?.toLowerCase().includes(input.toLowerCase())
                  }
                >
                  {statistics.feature_statistics.map(feature => (
                    <Option key={feature.feature_id} value={feature.feature_id}>
                      {feature.feature_name} ({feature.tagged_image_count} 张)
                    </Option>
                  ))}
                </Select>
              }
            >
              <Table
                columns={featureColumns}
                dataSource={statistics.feature_statistics}
                rowKey="feature_id"
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showTotal: (total) => `共 ${total} 条`
                }}
                onRow={(record) => ({
                  onClick: () => {
                    setSelectedFeatureId(record.feature_id)
                  },
                  style: {
                    cursor: 'pointer',
                    backgroundColor: selectedFeatureId === record.feature_id ? '#e6f7ff' : 'white'
                  }
                })}
              />
            </Card>

            {/* 特征打标图片数统计 */}
            {statistics.feature_statistics && statistics.feature_statistics.length > 0 && (
              <Card title="特征打标图片数统计（Top 10）" style={{ marginBottom: 24 }}>
                <Row gutter={[16, 16]}>
                  {statistics.feature_statistics.slice(0, 10).map((feature) => {
                    const maxCount = Math.max(...statistics.feature_statistics.map(f => f.tagged_image_count))
                    const percentage = maxCount > 0 ? (feature.tagged_image_count / maxCount) * 100 : 0
                    return (
                      <Col key={feature.feature_id} xs={24} sm={12} lg={8} xl={6}>
                        <Card size="small" title={feature.feature_name} style={{ height: '100%' }}>
                          <div style={{ marginBottom: 8 }}>
                            <div style={{ fontSize: 24, fontWeight: 'bold', color: '#1890ff' }}>
                              {feature.tagged_image_count}
                            </div>
                            <div style={{ fontSize: 12, color: '#999' }}>张图片</div>
                          </div>
                          <Progress 
                            percent={percentage} 
                            size="small"
                            strokeColor={{
                              '0%': '#108ee9',
                              '100%': '#87d068',
                            }}
                          />
                        </Card>
                      </Col>
                    )
                  })}
                </Row>
              </Card>
            )}

            {/* 特征值分布 */}
            {selectedFeatureId && featureDistribution && (
              <Card
                title={`${featureDistribution.feature_name} - 特征值分布`}
                loading={loadingDistribution}
              >
                {featureDistribution.distribution && featureDistribution.distribution.length > 0 ? (
                  <Row gutter={[16, 16]}>
                    {featureDistribution.distribution.slice(0, 20).map((item, idx) => {
                      const maxCount = Math.max(...featureDistribution.distribution.map(d => d.count))
                      const percentage = maxCount > 0 ? (item.count / maxCount) * 100 : 0
                      return (
                        <Col key={idx} xs={24} sm={12} lg={8} xl={6}>
                          <Card size="small" style={{ height: '100%' }}>
                            <div style={{ marginBottom: 8 }}>
                              <div style={{ 
                                fontSize: 16, 
                                fontWeight: 'bold',
                                marginBottom: 4,
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap'
                              }}>
                                {item.value}
                              </div>
                              <div style={{ fontSize: 20, fontWeight: 'bold', color: '#52c41a' }}>
                                {item.count}
                              </div>
                              <div style={{ fontSize: 12, color: '#999' }}>
                                {item.percentage}% / {featureDistribution.total_images} 张
                              </div>
                            </div>
                            <Progress 
                              percent={item.percentage} 
                              size="small"
                              strokeColor={{
                                '0%': '#108ee9',
                                '100%': '#87d068',
                              }}
                            />
                          </Card>
                        </Col>
                      )
                    })}
                  </Row>
                ) : (
                  <Empty description="暂无特征值数据" />
                )}
              </Card>
            )}
          </>
        )}
      </Spin>
    </div>
  )
}

export default FeatureAnalysis

