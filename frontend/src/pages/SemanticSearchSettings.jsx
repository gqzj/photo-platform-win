import React, { useState, useEffect } from 'react'
import { Card, Button, Statistic, Row, Col, Progress, message, Space, Alert } from 'antd'
import { PlayCircleOutlined, ReloadOutlined } from '@ant-design/icons'
import api from '../services/api'

const SemanticSearchSettings = () => {
  const [stats, setStats] = useState(null)
  const [encodingStatus, setEncodingStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [encodingLoading, setEncodingLoading] = useState(false)

  // 获取统计信息
  const fetchStats = async () => {
    setLoading(true)
    try {
      const response = await api.get('/semantic-search/stats')
      if (response.code === 200) {
        setStats(response.data)
        setEncodingStatus(response.data.encoding_task)
      } else {
        message.error(response.message || '获取统计信息失败')
      }
    } catch (error) {
      message.error('获取统计信息失败：' + (error.response?.data?.message || error.message))
    } finally {
      setLoading(false)
    }
  }

  // 获取编码任务状态
  const fetchEncodingStatus = async () => {
    try {
      const response = await api.get('/semantic-search/encode/status')
      if (response.code === 200) {
        setEncodingStatus(response.data)
      }
    } catch (error) {
      console.error('获取编码任务状态失败:', error)
    }
  }

  // 启动编码任务
  const handleStartEncoding = async () => {
    setEncodingLoading(true)
    try {
      const response = await api.post('/semantic-search/encode/start')
      if (response.code === 200) {
        message.success('编码任务已启动')
        // 开始轮询状态
        startPolling()
      } else {
        message.error(response.message || '启动编码任务失败')
      }
    } catch (error) {
      message.error('启动编码任务失败：' + (error.response?.data?.message || error.message))
    } finally {
      setEncodingLoading(false)
    }
  }

  // 轮询编码状态
  const startPolling = () => {
    const interval = setInterval(() => {
      fetchEncodingStatus()
      fetchStats()
      
      // 如果任务完成，停止轮询
      if (encodingStatus && !encodingStatus.running) {
        clearInterval(interval)
      }
    }, 2000) // 每2秒轮询一次

    // 30分钟后自动停止轮询
    setTimeout(() => {
      clearInterval(interval)
    }, 30 * 60 * 1000)
  }

  useEffect(() => {
    fetchStats()
    fetchEncodingStatus()
    
    // 如果任务正在运行，开始轮询
    if (encodingStatus && encodingStatus.running) {
      startPolling()
    }
  }, [])

  // 如果任务正在运行，定期更新状态
  useEffect(() => {
    let interval = null
    if (encodingStatus && encodingStatus.running) {
      interval = setInterval(() => {
        fetchEncodingStatus()
        fetchStats()
      }, 2000)
    }
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [encodingStatus?.running])

  const encodingProgress = encodingStatus && encodingStatus.total > 0
    ? (encodingStatus.processed / encodingStatus.total) * 100
    : 0

  return (
    <div style={{ padding: '24px' }}>
      <Card title="语义搜索设置" style={{ marginBottom: 16 }}>
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={8}>
            <Card>
              <Statistic
                title="总图片数"
                value={stats?.total_images || 0}
                loading={loading}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="已编码图片数"
                value={stats?.encoded_count || 0}
                loading={loading}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="未编码图片数"
                value={stats?.not_encoded_count || 0}
                loading={loading}
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={12}>
            <Card title="向量数据库统计">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <strong>集合名称：</strong>
                  {stats?.collection_stats?.collection_name || 'N/A'}
                </div>
                <div>
                  <strong>向量维度：</strong>
                  {stats?.collection_stats?.dimension || 'N/A'}
                </div>
                <div>
                  <strong>向量数量：</strong>
                  {stats?.collection_stats?.total_images || 0}
                </div>
              </Space>
            </Card>
          </Col>
          <Col span={12}>
            <Card title="编码任务">
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                {encodingStatus?.running ? (
                  <>
                    <Alert
                      message="编码任务正在运行中"
                      type="info"
                      showIcon
                    />
                    <div>
                      <div style={{ marginBottom: 8 }}>
                        <strong>进度：</strong>
                        {encodingStatus.processed} / {encodingStatus.total}
                      </div>
                      <Progress
                        percent={Math.round(encodingProgress)}
                        status="active"
                        format={(percent) => `${percent}%`}
                      />
                      <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                        成功: {encodingStatus.success} | 失败: {encodingStatus.failed}
                      </div>
                      {encodingStatus.current_image_id && (
                        <div style={{ marginTop: 4, fontSize: 12, color: '#999' }}>
                          当前处理: 图片ID {encodingStatus.current_image_id}
                        </div>
                      )}
                    </div>
                  </>
                ) : encodingStatus && encodingStatus.total > 0 ? (
                  <>
                    <Alert
                      message="编码任务已完成"
                      type="success"
                      showIcon
                    />
                    <div style={{ fontSize: 12, color: '#666' }}>
                      总计: {encodingStatus.total} | 
                      成功: {encodingStatus.success} | 
                      失败: {encodingStatus.failed}
                    </div>
                    {encodingStatus.error_message && (
                      <Alert
                        message="错误信息"
                        description={encodingStatus.error_message}
                        type="error"
                        style={{ marginTop: 8 }}
                      />
                    )}
                  </>
                ) : (
                  <Alert
                    message="暂无编码任务"
                    type="info"
                    showIcon
                  />
                )}
                
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={handleStartEncoding}
                  loading={encodingLoading}
                  disabled={encodingStatus?.running}
                  block
                >
                  {encodingStatus?.running ? '任务运行中' : '启动图片编码'}
                </Button>
                
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() => {
                    fetchStats()
                    fetchEncodingStatus()
                  }}
                  block
                >
                  刷新状态
                </Button>
              </Space>
            </Card>
          </Col>
        </Row>
      </Card>
    </div>
  )
}

export default SemanticSearchSettings
