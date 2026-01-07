import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  message,
  Popconfirm,
  Upload,
  Image,
  Progress,
  Tag,
  Select,
  Tooltip
} from 'antd'
import { UploadOutlined, DeleteOutlined, SearchOutlined, EyeOutlined, ExperimentOutlined, StarOutlined, FileImageOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

const { TextArea } = Input

const SampleImageManagement = () => {
  const navigate = useNavigate()
  const [dataSource, setDataSource] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  })
  const [filters, setFilters] = useState({
    keyword: ''
  })
  const [uploadModalVisible, setUploadModalVisible] = useState(false)
  const [uploadFileList, setUploadFileList] = useState([])
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [editingRecord, setEditingRecord] = useState(null)
  const [form] = Form.useForm()
  const [previewVisible, setPreviewVisible] = useState(false)
  const [previewImage, setPreviewImage] = useState('')
  const [lutApplicationStatus, setLutApplicationStatus] = useState({})
  const [statusPolling, setStatusPolling] = useState({})
  const [lutAestheticScoreStatus, setLutAestheticScoreStatus] = useState({})
  const [aestheticScoreModalVisible, setAestheticScoreModalVisible] = useState(false)
  const [scoringImageId, setScoringImageId] = useState(null)
  const [aestheticScorePolling, setAestheticScorePolling] = useState({})

  // 获取数据
  const fetchData = async (page = 1, pageSize = 20) => {
    setLoading(true)
    try {
      const params = {
        page,
        page_size: pageSize,
        ...filters
      }
      const response = await api.get('/sample-images', { params })
      if (response.code === 200) {
        setDataSource(response.data.list || [])
        setPagination({
          current: response.data.page,
          pageSize: response.data.page_size,
          total: response.data.total
        })
      } else {
        message.error(response.message || '获取数据失败')
      }
    } catch (error) {
      message.error('获取数据失败：' + (error.response?.data?.message || error.message))
      console.error('获取数据错误:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData(pagination.current, pagination.pageSize)
  }, [filters])

  // 获取所有图片的LUT应用状态
  useEffect(() => {
    const fetchAllStatuses = async () => {
      if (dataSource.length > 0) {
        const promises = dataSource.map(img => fetchLutApplicationStatus(img.id))
        await Promise.all(promises)
      }
    }
    fetchAllStatuses()
  }, [dataSource])

  // 获取所有图片的美学评分状态，并对运行中的任务启动轮询
  useEffect(() => {
    const fetchAllAestheticScoreStatuses = async () => {
      if (dataSource.length > 0) {
        const promises = dataSource.map(async (img) => {
          const status = await fetchLutAestheticScoreStatus(img.id)
          // 如果任务正在运行，启动轮询
          if (status && status.status === 'running') {
            startAestheticScorePolling(img.id)
          }
          return status
        })
        await Promise.all(promises)
      }
    }
    fetchAllAestheticScoreStatuses()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataSource])

  // 处理搜索
  const handleSearch = () => {
    setPagination(prev => ({ ...prev, current: 1 }))
    fetchData(1, pagination.pageSize)
  }

  // 打开上传模态框
  const handleOpenUploadModal = () => {
    setUploadModalVisible(true)
    setUploadFileList([])
  }

  // 处理上传
  const handleUpload = async () => {
    if (uploadFileList.length === 0) {
      message.warning('请选择要上传的图片')
      return
    }

    try {
      const formData = new FormData()
      uploadFileList.forEach(file => {
        formData.append('files', file.originFileObj || file)
      })

      const response = await api.post('/sample-images', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      if (response.code === 200) {
        message.success(response.message)
        setUploadModalVisible(false)
        setUploadFileList([])
        fetchData()
        if (response.data?.errors && response.data.errors.length > 0) {
          response.data.errors.forEach(err => {
            message.error(`${err.filename}: ${err.error}`)
          })
        }
      } else {
        message.error(response.message || '上传失败')
      }
    } catch (error) {
      message.error('上传失败：' + (error.response?.data?.message || error.message))
      console.error('上传错误:', error)
    }
  }

  // 打开编辑模态框
  const handleOpenEditModal = (record) => {
    setEditingRecord(record)
    form.setFieldsValue({
      description: record.description
    })
    setEditModalVisible(true)
  }

  // 提交编辑
  const handleEditSubmit = async () => {
    try {
      const values = await form.validateFields()
      const response = await api.put(`/sample-images/${editingRecord.id}`, values)
      if (response.code === 200) {
        message.success('更新成功')
        setEditModalVisible(false)
        fetchData()
      } else {
        message.error(response.message || '更新失败')
      }
    } catch (error) {
      if (error.errorFields) {
        return
      }
      message.error('操作失败：' + (error.response?.data?.message || error.message))
      console.error('操作错误:', error)
    }
  }

  // 删除
  const handleDelete = async (id) => {
    try {
      const response = await api.delete(`/sample-images/${id}`)
      if (response.code === 200) {
        message.success('删除成功')
        fetchData()
      } else {
        message.error(response.message || '删除失败')
      }
    } catch (error) {
      message.error('删除失败：' + (error.response?.data?.message || error.message))
      console.error('删除错误:', error)
    }
  }

  // 预览图片
  const handlePreview = (record) => {
    setPreviewImage(`/api/sample-images/${record.id}/content`)
    setPreviewVisible(true)
  }

  // 应用LUT
  const handleApplyLuts = async (imageId) => {
    try {
      const response = await api.post(`/sample-images/${imageId}/apply-luts`)
      if (response.code === 200) {
        message.success('LUT应用任务已启动')
        // 开始轮询状态
        startStatusPolling(imageId)
      } else {
        message.error(response.message || '启动失败')
      }
    } catch (error) {
      message.error('启动失败：' + (error.response?.data?.message || error.message))
      console.error('启动错误:', error)
    }
  }

  // 获取LUT应用状态
  const fetchLutApplicationStatus = async (imageId) => {
    try {
      const response = await api.get(`/sample-images/${imageId}/lut-application-status`)
      if (response.code === 200) {
        setLutApplicationStatus(prev => ({
          ...prev,
          [imageId]: response.data
        }))
        return response.data
      }
    } catch (error) {
      console.error('获取状态失败:', error)
    }
    return null
  }

  // 开始状态轮询
  const startStatusPolling = (imageId) => {
    // 清除之前的轮询
    if (statusPolling[imageId]) {
      clearInterval(statusPolling[imageId])
    }

    // 立即获取一次状态
    fetchLutApplicationStatus(imageId)

    // 设置轮询
    const interval = setInterval(async () => {
      const status = await fetchLutApplicationStatus(imageId)
      if (status && (status.status === 'completed' || status.status === 'failed')) {
        clearInterval(interval)
        setStatusPolling(prev => {
          const newPolling = { ...prev }
          delete newPolling[imageId]
          return newPolling
        })
      }
    }, 2000) // 每2秒轮询一次

    setStatusPolling(prev => ({
      ...prev,
      [imageId]: interval
    }))
  }

  // 组件卸载时清除所有轮询
  useEffect(() => {
    return () => {
      Object.values(statusPolling).forEach(interval => {
        if (interval) clearInterval(interval)
      })
    }
  }, [statusPolling])

  // 获取LUT应用后图片美学评分状态
  const fetchLutAestheticScoreStatus = async (imageId) => {
    try {
      const response = await api.get(`/sample-images/${imageId}/lut-applied-images/aesthetic-score-status`)
      if (response.code === 200) {
        setLutAestheticScoreStatus(prev => ({
          ...prev,
          [imageId]: response.data
        }))
        return response.data
      }
    } catch (error) {
      console.error('获取美学评分状态失败:', error)
    }
    return null
  }

  // 开始美学评分状态轮询
  const startAestheticScorePolling = (imageId) => {
    // 清除之前的轮询
    if (aestheticScorePolling[imageId]) {
      clearInterval(aestheticScorePolling[imageId])
    }

    // 立即获取一次状态
    fetchLutAestheticScoreStatus(imageId)

    // 设置轮询
    const interval = setInterval(async () => {
      const status = await fetchLutAestheticScoreStatus(imageId)
      if (status && (status.status === 'completed' || status.status === 'failed')) {
        clearInterval(interval)
        setAestheticScorePolling(prev => {
          const newPolling = { ...prev }
          delete newPolling[imageId]
          return newPolling
        })
      }
    }, 2000) // 每2秒轮询一次

    setAestheticScorePolling(prev => ({
      ...prev,
      [imageId]: interval
    }))
  }

  // 组件卸载时清除所有轮询
  useEffect(() => {
    return () => {
      Object.values(aestheticScorePolling).forEach(interval => {
        if (interval) clearInterval(interval)
      })
    }
  }, [aestheticScorePolling])

  // 打开美学评分模态框
  const handleOpenAestheticScoreModal = (imageId) => {
    setScoringImageId(imageId)
    setAestheticScoreModalVisible(true)
  }

  // 启动批量美学评分
  const handleStartAestheticScore = async (values) => {
    if (!scoringImageId) return
    
    try {
      const response = await api.post(`/sample-images/${scoringImageId}/lut-applied-images/aesthetic-score`, {
        evaluator_type: values.evaluator_type,
        score_mode: values.score_mode
      })
      if (response.code === 200) {
        message.success('美学评分任务已启动')
        setAestheticScoreModalVisible(false)
        // 开始轮询状态
        startAestheticScorePolling(scoringImageId)
      } else {
        message.error(response.message || '启动失败')
      }
    } catch (error) {
      message.error('启动失败：' + (error.response?.data?.message || error.message))
      console.error('启动错误:', error)
    }
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80
    },
    {
      title: '缩略图',
      dataIndex: 'id',
      key: 'thumbnail',
      width: 100,
      render: (id, record) => (
        <Image
          src={`/api/sample-images/${id}/content`}
          alt={record.original_filename}
          width={60}
          height={60}
          style={{ objectFit: 'cover', cursor: 'pointer' }}
          preview={false}
          onClick={() => handlePreview(record)}
        />
      )
    },
    {
      title: '原始文件名',
      dataIndex: 'original_filename',
      key: 'original_filename',
      ellipsis: true
    },
    {
      title: '尺寸',
      key: 'dimensions',
      width: 120,
      render: (_, record) => {
        if (record.width && record.height) {
          return `${record.width} × ${record.height}`
        }
        return '-'
      }
    },
    {
      title: '格式',
      dataIndex: 'format',
      key: 'format',
      width: 80,
      render: (format) => format ? format.toUpperCase() : '-'
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 120,
      render: (size) => {
        if (!size) return '-'
        const units = ['B', 'KB', 'MB', 'GB']
        let unitIndex = 0
        let fileSize = size
        while (fileSize >= 1024 && unitIndex < units.length - 1) {
          fileSize /= 1024
          unitIndex++
        }
        return `${fileSize.toFixed(2)} ${units[unitIndex]}`
      }
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180
    },
    {
      title: 'LUT应用进度',
      key: 'lut_progress',
      width: 200,
      render: (_, record) => {
        const status = lutApplicationStatus[record.id]
        if (!status) {
          return '-'
        }
        
        if (status.status === 'running') {
          const percent = status.total_lut_count > 0 
            ? Math.round((status.processed_lut_count / status.total_lut_count) * 100)
            : 0
          return (
            <div>
              <Progress 
                percent={percent} 
                size="small" 
                status="active"
                format={() => `${status.processed_lut_count}/${status.total_lut_count}`}
              />
            </div>
          )
        } else if (status.status === 'completed') {
          const hasError = status.error_message
          return (
            <div>
              <Tag color={hasError ? "warning" : "success"}>
                {hasError ? "部分完成" : "已完成"} ({status.processed_lut_count}/{status.total_lut_count})
              </Tag>
              {hasError && (
                <Tooltip title={status.error_message}>
                  <Button 
                    type="link" 
                    size="small" 
                    icon={<ExclamationCircleOutlined />}
                    onClick={() => {
                      Modal.warning({
                        title: 'LUT应用任务完成（部分失败）',
                        content: (
                          <div style={{ maxHeight: '400px', overflow: 'auto', whiteSpace: 'pre-wrap' }}>
                            {status.error_message}
                          </div>
                        ),
                        width: 600
                      })
                    }}
                  >
                    查看详情
                  </Button>
                </Tooltip>
              )}
            </div>
          )
        } else if (status.status === 'failed') {
          return (
            <Tag color="error">失败</Tag>
          )
        } else if (status.status === 'pending') {
          return (
            <Tag color="default">等待中</Tag>
          )
        }
        return '-'
      }
    },
    {
      title: '美学评分进度',
      key: 'aesthetic_score_progress',
      width: 200,
      render: (_, record) => {
        const status = lutAestheticScoreStatus[record.id]
        if (!status) {
          return '-'
        }
        
        if (status.status === 'running') {
          const percent = status.total_image_count > 0 
            ? Math.round((status.processed_image_count / status.total_image_count) * 100)
            : 0
          return (
            <div>
              <Progress 
                percent={percent} 
                size="small" 
                status="active"
                format={() => `${status.processed_image_count}/${status.total_image_count}`}
              />
            </div>
          )
        } else if (status.status === 'completed') {
          return (
            <Tag color="success">
              已完成 ({status.processed_image_count}/{status.total_image_count})
            </Tag>
          )
        } else if (status.status === 'failed') {
          return (
            <Tag color="error">失败</Tag>
          )
        } else if (status.status === 'pending') {
          return (
            <Tag color="default">等待中</Tag>
          )
        }
        return '-'
      }
    },
    {
      title: '操作',
      key: 'action',
      width: 250,
      fixed: 'right',
      render: (_, record) => {
        const status = lutApplicationStatus[record.id]
        const isRunning = status && status.status === 'running'
        
        return (
          <Space wrap>
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handlePreview(record)}
            >
              预览
            </Button>
            <Button
              type="link"
              size="small"
              icon={<ExperimentOutlined />}
              onClick={() => handleApplyLuts(record.id)}
              disabled={isRunning}
            >
              应用LUT
            </Button>
            <Button
              type="link"
              size="small"
              icon={<FileImageOutlined />}
              onClick={() => navigate(`/lut-analysis/sample-images/${record.id}/lut-results`)}
            >
              查看LUT结果
            </Button>
            <Button
              type="link"
              size="small"
              icon={<StarOutlined />}
              onClick={() => handleOpenAestheticScoreModal(record.id)}
              disabled={lutAestheticScoreStatus[record.id]?.status === 'running'}
            >
              批量美学评分
            </Button>
            <Button
              type="link"
              size="small"
              onClick={() => handleOpenEditModal(record)}
            >
              编辑
            </Button>
            <Popconfirm
              title="确定要删除这张图片吗？"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="link"
                danger
                size="small"
                icon={<DeleteOutlined />}
              >
                删除
              </Button>
            </Popconfirm>
          </Space>
        )
      }
    }
  ]

  return (
    <div>
      <Card
        title="样本图片管理"
        extra={
          <Button
            type="primary"
            icon={<UploadOutlined />}
            onClick={handleOpenUploadModal}
          >
            批量上传
          </Button>
        }
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Space>
            <Input
              placeholder="搜索文件名"
              value={filters.keyword}
              onChange={(e) => setFilters(prev => ({ ...prev, keyword: e.target.value }))}
              style={{ width: 200 }}
              allowClear
            />
            <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
              搜索
            </Button>
          </Space>

          <Table
            columns={columns}
            dataSource={dataSource}
            loading={loading}
            rowKey="id"
            scroll={{ x: 'max-content' }}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: pagination.total,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 条`,
              onChange: (page, pageSize) => {
                setPagination(prev => ({ ...prev, current: page, pageSize }))
                fetchData(page, pageSize)
              }
            }}
          />
        </Space>
      </Card>

      {/* 上传模态框 */}
      <Modal
        title="批量上传样本图片"
        open={uploadModalVisible}
        onOk={handleUpload}
        onCancel={() => {
          setUploadModalVisible(false)
          setUploadFileList([])
        }}
        width={600}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Upload
            multiple
            fileList={uploadFileList}
            onChange={({ fileList }) => setUploadFileList(fileList)}
            beforeUpload={() => false}
            accept="image/*"
            listType="picture-card"
          >
            <div>
              <UploadOutlined />
              <div style={{ marginTop: 8 }}>选择图片</div>
            </div>
          </Upload>
          <div style={{ color: '#999', fontSize: 12 }}>
            支持的文件格式：JPG, JPEG, PNG, GIF, BMP, WEBP
          </div>
        </Space>
      </Modal>

      {/* 编辑模态框 */}
      <Modal
        title="编辑样本图片"
        open={editModalVisible}
        onOk={handleEditSubmit}
        onCancel={() => setEditModalVisible(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={4} placeholder="输入描述" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 图片预览 */}
      <Modal
        open={previewVisible}
        footer={null}
        onCancel={() => setPreviewVisible(false)}
        width={800}
        centered
      >
        <img alt="预览" style={{ width: '100%' }} src={previewImage} />
      </Modal>

      {/* 美学评分模态框 */}
      <Modal
        title="样本图片美学评分"
        open={aestheticScoreModalVisible}
        onOk={() => {
          const form = document.querySelector('#aesthetic-score-form')
          if (form) {
            form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }))
          }
        }}
        onCancel={() => {
          setAestheticScoreModalVisible(false)
          setScoringImageId(null)
        }}
        width={500}
      >
        <Form
          id="aesthetic-score-form"
          layout="vertical"
          onFinish={handleStartAestheticScore}
          initialValues={{
            evaluator_type: 'artimuse',
            score_mode: 'score_and_reason'
          }}
        >
          <Form.Item
            name="evaluator_type"
            label="评分器类型"
            rules={[{ required: true, message: '请选择评分器类型' }]}
          >
            <Select>
              <Select.Option value="artimuse">ArtiMuse</Select.Option>
              <Select.Option value="q_insight" disabled>Q-Insight (暂未实现)</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="score_mode"
            label="评分模式"
            rules={[{ required: true, message: '请选择评分模式' }]}
          >
            <Select>
              <Select.Option value="score_only">仅评分</Select.Option>
              <Select.Option value="score_and_reason">评分和理由</Select.Option>
            </Select>
          </Form.Item>
          <div style={{ marginTop: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
            <div style={{ fontSize: 12, color: '#999' }}>将对该样本图片的所有LUT应用后的图片进行批量美学评分</div>
          </div>
        </Form>
      </Modal>
    </div>
  )
}

export default SampleImageManagement

