import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Steps,
  Button,
  Space,
  Tag,
  Descriptions,
  message,
  Popconfirm,
  Spin,
  Empty,
  Divider,
  Dropdown,
  Menu,
  Switch,
  Progress
} from 'antd'
import {
  PlayCircleOutlined,
  ReloadOutlined,
  ArrowLeftOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  SyncOutlined,
  ThunderboltOutlined
} from '@ant-design/icons'
import api from '../services/api'

const { Step } = Steps

const RequirementProgress = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [requirement, setRequirement] = useState(null)
  const [progressData, setProgressData] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [autoExecute, setAutoExecute] = useState(false)
  const [isExecuting, setIsExecuting] = useState(false)

  // 获取需求详情
  const fetchRequirement = async () => {
    try {
      const response = await api.get(`/requirements/${id}`)
      if (response.code === 200) {
        setRequirement(response.data)
      } else {
        message.error(response.message || '获取需求详情失败')
      }
    } catch (error) {
      message.error('获取需求详情失败：' + (error.response?.data?.message || error.message))
    }
  }

  // 获取进度数据
  const fetchProgress = async () => {
    setLoading(true)
    try {
      const response = await api.get(`/requirements/${id}/progress`)
      if (response.code === 200) {
        setProgressData(response.data)
        // 如果有运行中的任务，开启自动刷新（如果开启了自动执行，则保持开启）
        const hasRunningTask = response.data.tasks?.some(t => t.status === 'running')
        if (hasRunningTask || autoExecute) {
          setAutoRefresh(true)
        }
        
        // 如果开启了自动执行，检查是否所有任务都已完成
        if (autoExecute) {
          const allCompleted = response.data.tasks?.every(t => t.status === 'completed')
          if (allCompleted) {
            // 更新需求状态为完成
            try {
              await api.put(`/requirements/${id}`, { status: 'completed' })
              await fetchRequirement() // 刷新需求信息
            } catch (error) {
              console.error('更新需求状态失败:', error)
            }
            setAutoExecute(false)
            setAutoRefresh(false)
            message.success('所有任务已完成，需求状态已更新为完成')
          }
        }
      } else {
        message.error(response.message || '获取进度失败')
      }
    } catch (error) {
      message.error('获取进度失败：' + (error.response?.data?.message || error.message))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRequirement()
    fetchProgress()
  }, [id])

  // 自动刷新和自动执行
  useEffect(() => {
    let interval = null
    if (autoRefresh || autoExecute) {
      interval = setInterval(async () => {
        // 先获取最新的进度数据
        const progressResponse = await api.get(`/requirements/${id}/progress`)
        if (progressResponse.code === 200) {
          const latestProgressData = progressResponse.data
          setProgressData(latestProgressData)
          
          // 如果开启了自动执行，检查是否可以执行下一个任务
          if (autoExecute && !isExecuting) {
            // 检查是否有任务完成，且可以执行下一个任务
            if (latestProgressData.can_execute_next) {
              // 检查是否有运行中的任务
              const hasRunningTask = latestProgressData.tasks?.some(t => t.status === 'running')
              
              // 如果没有运行中的任务，且可以执行下一个，则自动执行
              if (!hasRunningTask) {
                setIsExecuting(true)
                try {
                  const response = await api.post(`/requirements/${id}/execute-next`)
                  if (response.code === 200) {
                    // 刷新数据
                    await fetchProgress()
                    await fetchRequirement()
                    setAutoRefresh(true)
                    
                    // 检查是否所有任务都已完成
                    if (response.data?.all_completed) {
                      // 更新需求状态为完成
                      try {
                        await api.put(`/requirements/${id}`, { status: 'completed' })
                        await fetchRequirement() // 刷新需求信息
                      } catch (error) {
                        console.error('更新需求状态失败:', error)
                      }
                      setAutoExecute(false)
                      message.success('所有任务已完成，需求状态已更新为完成！')
                    }
                  } else {
                    message.error(response.message || '执行失败')
                    setAutoExecute(false)
                  }
                } catch (error) {
                  console.error('自动执行任务失败:', error)
                  message.error('自动执行失败：' + (error.response?.data?.message || error.message))
                  setAutoExecute(false)
                } finally {
                  setIsExecuting(false)
                }
              }
            } else {
              // 检查是否所有任务都已完成
              const allCompleted = latestProgressData.tasks?.every(t => t.status === 'completed')
              if (allCompleted) {
                // 所有任务完成，更新需求状态为完成
                try {
                  await api.put(`/requirements/${id}`, { status: 'completed' })
                  await fetchRequirement() // 刷新需求信息
                } catch (error) {
                  console.error('更新需求状态失败:', error)
                }
                // 关闭自动执行
                setAutoExecute(false)
                setAutoRefresh(false)
                message.success('所有任务已完成，需求状态已更新为完成')
              }
            }
          } else {
            // 只是刷新数据
            await fetchRequirement()
          }
        }
      }, 5000) // 每5秒刷新一次
    }
    return () => {
      if (interval) {
        clearInterval(interval)
      }
    }
  }, [autoRefresh, autoExecute, isExecuting, id])

  // 执行下一个任务
  const handleExecuteNext = async () => {
    try {
      const response = await api.post(`/requirements/${id}/execute-next`)
      if (response.code === 200) {
        const msg = response.message || '任务已启动'
        if (!autoExecute) {
          // 只有在非自动执行模式下才显示消息，避免消息过多
          message.success(msg)
        }
        await fetchProgress()
        await fetchRequirement()
        setAutoRefresh(true)
        
        // 如果开启了自动执行，检查是否所有任务都已完成
        if (response.data?.all_completed) {
          // 更新需求状态为完成
          try {
            await api.put(`/requirements/${id}`, { status: 'completed' })
            await fetchRequirement() // 刷新需求信息
          } catch (error) {
            console.error('更新需求状态失败:', error)
          }
          setAutoExecute(false)
          message.success('所有任务已完成，需求状态已更新为完成！')
        }
      } else {
        message.error(response.message || '执行失败')
        // 如果执行失败，关闭自动执行
        if (autoExecute) {
          setAutoExecute(false)
        }
      }
    } catch (error) {
      const errorMsg = '执行失败：' + (error.response?.data?.message || error.message)
      message.error(errorMsg)
      // 如果执行失败，关闭自动执行
      if (autoExecute) {
        setAutoExecute(false)
      }
    }
  }

  // 重试任务
  const handleRetryTask = async (task) => {
    try {
      // 先重置任务状态
      const retryResponse = await api.post(`/requirements/${id}/tasks/${task.id}/retry`)
      if (retryResponse.code === 200) {
        message.success('任务已重置')
        await fetchProgress()
        
        // 然后执行该任务
        try {
          let executeResponse
          if (task.task_type === 'crawler') {
            executeResponse = await api.post(`/crawler/tasks/${task.task_id}/crawl`)
          } else if (task.task_type === 'cleaning') {
            executeResponse = await api.post(`/data-cleaning/tasks/${task.task_id}/execute`)
          } else if (task.task_type === 'tagging') {
            executeResponse = await api.post(`/tagging/tasks/${task.task_id}/execute`)
          } else if (task.task_type === 'sample_set') {
            executeResponse = await api.post(`/sample-sets/${task.task_id}/calculate`)
          }
          
          if (executeResponse && executeResponse.code === 200) {
            message.success('任务已重新启动')
            await fetchProgress()
            setAutoRefresh(true)
          }
        } catch (executeError) {
          // 执行失败不影响重置成功
          console.error('执行任务失败:', executeError)
        }
      } else {
        message.error(retryResponse.message || '重置失败')
      }
    } catch (error) {
      message.error('重试失败：' + (error.response?.data?.message || error.message))
    }
  }

  // 更新任务状态
  const handleUpdateStatus = async (task, newStatus) => {
    try {
      const response = await api.put(`/requirements/${id}/tasks/${task.id}/update-status`, {
        status: newStatus
      })
      if (response.code === 200) {
        message.success('状态更新成功')
        await fetchProgress()
        await fetchRequirement()
      } else {
        message.error(response.message || '更新失败')
      }
    } catch (error) {
      message.error('更新失败：' + (error.response?.data?.message || error.message))
    }
  }

  // 手动刷新
  const handleRefresh = () => {
    fetchProgress()
    fetchRequirement()
  }

  // 任务类型映射
  const taskTypeMap = {
    'crawler': { name: '抓取任务', icon: <PlayCircleOutlined />, color: '#1890ff' },
    'cleaning': { name: '清洗任务', icon: <SyncOutlined />, color: '#52c41a' },
    'tagging': { name: '打标任务', icon: <CheckCircleOutlined />, color: '#faad14' },
    'sample_set': { name: '样本集', icon: <ReloadOutlined />, color: '#722ed1' }
  }

  // 状态映射
  const statusMap = {
    'pending': { color: 'default', text: '待执行', icon: <ClockCircleOutlined /> },
    'running': { color: 'processing', text: '执行中', icon: <SyncOutlined spin /> },
    'completed': { color: 'success', text: '已完成', icon: <CheckCircleOutlined /> },
    'failed': { color: 'error', text: '失败', icon: <CloseCircleOutlined /> }
  }

  if (loading && !progressData) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!requirement) {
    return (
      <div style={{ padding: '24px' }}>
        <Empty description="需求不存在" />
      </div>
    )
  }

  const currentStep = progressData?.current_task_order || 0
  const tasks = progressData?.tasks || []

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <Space>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/requirement/management')}
            >
              返回
            </Button>
            <span>需求进度：{requirement.name}</span>
          </Space>
        }
        extra={
          <Space>
            <Space>
              <ThunderboltOutlined style={{ color: autoExecute ? '#1890ff' : '#999' }} />
              <span style={{ marginRight: 8 }}>自动执行</span>
              <Switch
                checked={autoExecute}
                onChange={(checked) => {
                  setAutoExecute(checked)
                  if (checked) {
                    message.info('已开启自动执行，系统将自动检测任务状态并执行下一个任务')
                    setAutoRefresh(true) // 开启自动刷新
                  } else {
                    message.info('已关闭自动执行')
                  }
                }}
                disabled={requirement?.status === 'completed'}
              />
            </Space>
            <Button icon={<ReloadOutlined />} onClick={handleRefresh} loading={loading}>
              刷新
            </Button>
            {progressData?.can_execute_next && !autoExecute && (
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={handleExecuteNext}
                disabled={isExecuting}
              >
                执行下一个任务
              </Button>
            )}
            {autoExecute && isExecuting && (
              <Button type="primary" loading>
                正在执行...
              </Button>
            )}
          </Space>
        }
      >
        {/* 需求基本信息 */}
        <Descriptions title="需求信息" bordered column={2} style={{ marginBottom: 24 }}>
          <Descriptions.Item label="需求名称">{requirement.name}</Descriptions.Item>
          <Descriptions.Item label="需求发起人">{requirement.requester || '无'}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={requirement.status === 'active' ? 'processing' : requirement.status === 'completed' ? 'success' : 'default'}>
              {requirement.status === 'pending' ? '待处理' : 
               requirement.status === 'active' ? '进行中' : 
               requirement.status === 'completed' ? '已完成' : 
               requirement.status === 'cancelled' ? '已取消' : requirement.status}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="进度">
            {progressData ? (
              <span>
                {progressData.completed_tasks} / {progressData.total_tasks} 个任务已完成
              </span>
            ) : '-'}
          </Descriptions.Item>
        </Descriptions>

        {/* 进度步骤条 */}
        {tasks.length > 0 && (
          <div style={{ marginBottom: 24 }}>
            <Steps
              current={currentStep - 1}
              status={tasks.some(t => t.status === 'failed') ? 'error' : 'process'}
              style={{ marginTop: 24 }}
            >
              {tasks.map((task, index) => {
                const taskType = taskTypeMap[task.task_type] || { name: task.task_type, icon: null, color: '#999' }
                const statusInfo = statusMap[task.status] || { color: 'default', text: task.status, icon: null }
                
                let stepStatus = 'wait'
                if (task.status === 'completed') {
                  stepStatus = 'finish'
                } else if (task.status === 'running') {
                  stepStatus = 'process'
                } else if (task.status === 'failed') {
                  stepStatus = 'error'
                }

                return (
                  <Step
                    key={task.id}
                    title={taskType.name}
                    description={
                      <div>
                        <div style={{ marginBottom: 4 }}>
                          <Tag color={statusInfo.color} icon={statusInfo.icon}>
                            {statusInfo.text}
                          </Tag>
                        </div>
                        {task.name && (
                          <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                            {task.name}
                          </div>
                        )}
                      </div>
                    }
                    status={stepStatus}
                    icon={taskType.icon}
                  />
                )
              })}
            </Steps>
          </div>
        )}

        <Divider />

        {/* 任务详情列表 */}
        {tasks.length > 0 ? (
          <div>
            <h3 style={{ marginBottom: 16 }}>任务详情</h3>
            {tasks.map((task, index) => {
              const taskType = taskTypeMap[task.task_type] || { name: task.task_type, icon: null, color: '#999' }
              const statusInfo = statusMap[task.status] || { color: 'default', text: task.status, icon: null }
              
              // 判断是否可以执行（前置任务都已完成）
              const canExecute = index === 0 || tasks.slice(0, index).every(t => t.status === 'completed')
              
              return (
                <Card
                  key={task.id}
                  style={{
                    marginBottom: 16,
                    borderLeft: `4px solid ${taskType.color}`,
                    backgroundColor: task.status === 'running' ? '#e6f7ff' : '#fff'
                  }}
                  title={
                    <Space>
                      <span style={{ fontWeight: 'bold' }}>步骤 {task.order}: {taskType.name}</span>
                      <Tag color={statusInfo.color} icon={statusInfo.icon}>
                        {statusInfo.text}
                      </Tag>
                    </Space>
                  }
                  extra={
                    <Space>
                      {task.status === 'failed' && (
                        <Popconfirm
                          title="确定要重试这个任务吗？"
                          onConfirm={() => handleRetryTask(task)}
                          okText="确定"
                          cancelText="取消"
                        >
                          <Button
                            type="link"
                            icon={<ReloadOutlined />}
                            size="small"
                          >
                            重试
                          </Button>
                        </Popconfirm>
                      )}
                      {task.status === 'pending' && canExecute && (
                        <Button
                          type="link"
                          icon={<PlayCircleOutlined />}
                          size="small"
                          onClick={() => handleExecuteNext()}
                        >
                          执行
                        </Button>
                      )}
                      {task.status === 'running' && (
                        <Tag color="processing">执行中...</Tag>
                      )}
                      {/* 状态更新下拉菜单 */}
                      <Dropdown
                        menu={{
                          items: [
                            {
                              key: 'pending',
                              label: '设为待执行',
                              disabled: task.status === 'pending',
                              onClick: () => handleUpdateStatus(task, 'pending')
                            },
                            {
                              key: 'running',
                              label: '设为执行中',
                              disabled: task.status === 'running',
                              onClick: () => handleUpdateStatus(task, 'running')
                            },
                            {
                              key: 'completed',
                              label: '设为已完成',
                              disabled: task.status === 'completed',
                              onClick: () => handleUpdateStatus(task, 'completed')
                            },
                            {
                              key: 'failed',
                              label: '设为失败',
                              disabled: task.status === 'failed',
                              onClick: () => handleUpdateStatus(task, 'failed')
                            }
                          ]
                        }}
                        trigger={['click']}
                      >
                        <Button type="link" size="small">
                          更新状态
                        </Button>
                      </Dropdown>
                    </Space>
                  }
                >
                  <Descriptions column={2} size="small">
                    <Descriptions.Item label="任务ID">{task.task_id}</Descriptions.Item>
                    <Descriptions.Item label="任务名称">{task.name || '-'}</Descriptions.Item>
                    <Descriptions.Item label="开始时间">{task.started_at || '-'}</Descriptions.Item>
                    <Descriptions.Item label="完成时间">{task.finished_at || '-'}</Descriptions.Item>
                  </Descriptions>
                  
                  {/* 显示任务详细信息 */}
                  {task.detail && (
                    <div style={{ marginTop: 12 }}>
                      {task.task_type === 'crawler' && task.detail && (
                        <div>
                          <div style={{ fontSize: 12, color: '#999' }}>
                            已处理帖子: {task.detail.processed_posts || 0} | 
                            已处理评论: {task.detail.processed_comments || 0} | 
                            已下载媒体: {task.detail.downloaded_media || 0}
                          </div>
                        </div>
                      )}
                      {task.task_type === 'cleaning' && task.detail && (
                        <div>
                          <div style={{ fontSize: 12, color: '#999', marginBottom: 4 }}>
                            进度: {task.detail.processed_count || 0} / {task.detail.total_count || 0}
                            {task.detail.total_count > 0 && (
                              <span> ({Math.round(((task.detail.processed_count || 0) / task.detail.total_count) * 100)}%)</span>
                            )}
                          </div>
                          {task.detail.total_count > 0 && (
                            <Progress 
                              percent={Math.round(((task.detail.processed_count || 0) / task.detail.total_count) * 100)} 
                              size="small"
                              status={task.status === 'running' ? 'active' : task.status === 'completed' ? 'success' : 'normal'}
                            />
                          )}
                        </div>
                      )}
                      {task.task_type === 'tagging' && task.detail && (
                        <div>
                          <div style={{ fontSize: 12, color: '#999' }}>
                            进度: {task.detail.processed_count || 0} / {task.detail.total_count || 0} 
                            ({task.detail.progress || 0}%)
                          </div>
                        </div>
                      )}
                      {task.task_type === 'sample_set' && task.detail && (
                        <div>
                          <div style={{ fontSize: 12, color: '#999' }}>
                            图片数量: {task.detail.image_count || 0}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </Card>
              )
            })}
          </div>
        ) : (
          <Empty description="暂无任务" />
        )}
      </Card>
    </div>
  )
}

export default RequirementProgress

