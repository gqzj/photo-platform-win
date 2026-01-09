import React, { useState, useEffect, useRef } from 'react'
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
  Tag,
  Select,
  Upload,
  Progress,
  Alert,
  Image
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, UploadOutlined, DownloadOutlined, FolderOutlined, ExperimentOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Option } = Select
const { TextArea } = Input

const LutFileManagement = () => {
  const [dataSource, setDataSource] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  })
  const [filters, setFilters] = useState({
    keyword: '',
    category_id: undefined,
    tone: undefined,
    saturation: undefined,
    contrast: undefined
  })
  const [modalVisible, setModalVisible] = useState(false)
  const [editingRecord, setEditingRecord] = useState(null)
  const [form] = Form.useForm()
  const [categories, setCategories] = useState([])
  const [categoryModalVisible, setCategoryModalVisible] = useState(false)
  const [categoryForm] = Form.useForm()
  const [uploadModalVisible, setUploadModalVisible] = useState(false)
  const [uploadFileList, setUploadFileList] = useState([])
  const [uploadCategoryId, setUploadCategoryId] = useState(undefined)
  const [filenameStartIndex, setFilenameStartIndex] = useState(undefined)
  const [batchAnalyzeStatus, setBatchAnalyzeStatus] = useState(null)
  const [analyzePollingInterval, setAnalyzePollingInterval] = useState(null)
  const previousStatusRef = useRef(null) // 用于跟踪上一次的状态，避免重复提示
  const isInitialLoadRef = useRef(true) // 用于标记是否是首次加载

  // 获取分类列表
  const fetchCategories = async () => {
    try {
      const response = await api.get('/lut-categories/all')
      if (response.code === 200) {
        setCategories(response.data || [])
      }
    } catch (error) {
      console.error('获取分类列表失败:', error)
    }
  }

  useEffect(() => {
    fetchCategories()
  }, [])

  // 获取数据
  const fetchData = async (page = 1, pageSize = 20) => {
    setLoading(true)
    try {
      const params = {
        page,
        page_size: pageSize,
        ...filters
      }
      const response = await api.get('/lut-files', { params })
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

  // 处理搜索
  const handleSearch = () => {
    setPagination(prev => ({ ...prev, current: 1 }))
    fetchData(1, pagination.pageSize)
  }

  // 打开上传模态框
  const handleOpenUploadModal = () => {
    setUploadModalVisible(true)
    setUploadFileList([])
    setUploadCategoryId(undefined)
    setFilenameStartIndex(undefined)
  }

  // 处理文件名截断
  const truncateFilename = (filename, startIndex) => {
    if (startIndex === undefined || startIndex === null || startIndex === '') {
      return filename
    }
    const index = parseInt(startIndex)
    if (isNaN(index) || index < 0) {
      return filename
    }
    if (index >= filename.length) {
      return filename
    }
    return filename.substring(index)
  }

  // 处理上传
  const handleUpload = async () => {
    if (uploadFileList.length === 0) {
      message.warning('请选择要上传的文件')
      return
    }

    try {
      const formData = new FormData()
      const customFilenames = []
      
      uploadFileList.forEach(file => {
        const fileObj = file.originFileObj || file
        formData.append('files', fileObj)
        
        // 如果设置了截断起始位置，计算截断后的文件名
        if (filenameStartIndex !== undefined && filenameStartIndex !== null && filenameStartIndex !== '') {
          const truncatedName = truncateFilename(fileObj.name, filenameStartIndex)
          customFilenames.push(truncatedName)
        } else {
          customFilenames.push(fileObj.name)
        }
      })
      
      // 将自定义文件名数组作为JSON字符串传递
      if (filenameStartIndex !== undefined && filenameStartIndex !== null && filenameStartIndex !== '') {
        formData.append('custom_filenames', JSON.stringify(customFilenames))
      }
      
      if (uploadCategoryId) {
        formData.append('category_id', uploadCategoryId)
      }

      const response = await api.post('/lut-files', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      if (response.code === 200) {
        message.success(response.message)
        setUploadModalVisible(false)
        setUploadFileList([])
        fetchData()
        fetchCategories()
      } else {
        message.error(response.message || '上传失败')
        if (response.data?.errors && response.data.errors.length > 0) {
          response.data.errors.forEach(err => {
            message.error(`${err.filename}: ${err.error}`)
          })
        }
      }
    } catch (error) {
      message.error('上传失败：' + (error.response?.data?.message || error.message))
      console.error('上传错误:', error)
    }
  }

  // 打开编辑模态框
  const handleOpenModal = (record = null) => {
    setEditingRecord(record)
    if (record) {
      form.setFieldsValue({
        category_id: record.category_id,
        original_filename: record.original_filename,
        description: record.description
      })
    } else {
      form.resetFields()
    }
    setModalVisible(true)
  }

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editingRecord) {
        const response = await api.put(`/lut-files/${editingRecord.id}`, values)
        if (response.code === 200) {
          message.success('更新成功')
          setModalVisible(false)
          fetchData()
        } else {
          message.error(response.message || '更新失败')
        }
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
      const response = await api.delete(`/lut-files/${id}`)
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

  // 下载文件
  const handleDownload = async (id, filename) => {
    try {
      const response = await api.get(`/lut-files/${id}/download`, {
        responseType: 'blob'
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      message.success('下载成功')
    } catch (error) {
      message.error('下载失败：' + (error.response?.data?.message || error.message))
      console.error('下载错误:', error)
    }
  }

  // 分析LUT文件
  const handleAnalyze = async (id) => {
    try {
      const response = await api.post(`/lut-files/${id}/analyze`)
      if (response.code === 200) {
        message.success('分析成功')
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error(response.message || '分析失败')
      }
    } catch (error) {
      message.error('分析失败：' + (error.response?.data?.message || error.message))
      console.error('分析错误:', error)
    }
  }

  // 批量分析LUT文件
  const handleBatchAnalyze = async (skipAnalyzed = true, forceRestart = false) => {
    // 检查是否有运行中的任务
    if (batchAnalyzeStatus && batchAnalyzeStatus.status === 'running') {
      Modal.confirm({
        title: '确认重新启动',
        content: '当前有运行中的批量分析任务，是否要强制重新启动？这将中断当前任务。',
        okText: '确认重启',
        cancelText: '取消',
        okButtonProps: { danger: true },
        onOk: async () => {
          try {
            const response = await api.post('/lut-files/batch-analyze', {
              skip_analyzed: skipAnalyzed,
              force_restart: true
            })
            if (response.code === 200) {
              message.success('批量分析任务已重新启动')
              // 开始轮询状态
              fetchBatchAnalyzeStatus()
              startAnalyzePolling()
            } else {
              message.error(response.message || '启动批量分析失败')
            }
          } catch (error) {
            message.error('启动批量分析失败：' + (error.response?.data?.message || error.message))
            console.error('批量分析错误:', error)
          }
        }
      })
      return
    }

    try {
      const response = await api.post('/lut-files/batch-analyze', {
        skip_analyzed: skipAnalyzed,
        force_restart: forceRestart
      })
      if (response.code === 200) {
        message.success('批量分析任务已启动')
        // 开始轮询状态
        fetchBatchAnalyzeStatus()
        startAnalyzePolling()
      } else {
        message.error(response.message || '启动批量分析失败')
      }
    } catch (error) {
      message.error('启动批量分析失败：' + (error.response?.data?.message || error.message))
      console.error('批量分析错误:', error)
    }
  }

  // 重新分析（强制重新启动，重新分析所有文件）
  const handleRestartAnalyze = async () => {
    Modal.confirm({
      title: '确认重新分析',
      content: '将重新分析所有.cube格式的LUT文件，包括已分析过的文件。是否继续？',
      onOk: () => {
        handleBatchAnalyze(false, true) // skip_analyzed=false, force_restart=true
      }
    })
  }

  // 中断批量分析任务
  const handleInterruptAnalyze = async () => {
    Modal.confirm({
      title: '确认中断任务',
      content: '确定要中断当前正在执行的批量分析任务吗？任务将在处理完当前文件后停止。',
      okText: '确认中断',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          const response = await api.post('/lut-files/batch-analyze-interrupt')
          if (response.code === 200) {
            message.success('中断请求已发送')
            // 继续轮询以获取最新状态
            fetchBatchAnalyzeStatus()
          } else {
            message.error(response.message || '中断任务失败')
          }
        } catch (error) {
          message.error('中断任务失败：' + (error.response?.data?.message || error.message))
          console.error('中断任务错误:', error)
        }
      }
    })
  }

  // 获取批量分析状态
  const fetchBatchAnalyzeStatus = async () => {
    try {
      const response = await api.get('/lut-files/batch-analyze-status')
      if (response.code === 200) {
        const newStatus = response.data
        const previousStatus = previousStatusRef.current
        const isInitialLoad = isInitialLoadRef.current
        
        // 如果任务已完成或失败，停止轮询
        if (newStatus && (newStatus.status === 'completed' || newStatus.status === 'failed')) {
          stopAnalyzePolling()
          
          // 只在状态从非 completed/failed 变为 completed/failed 时才显示提示
          // 首次加载时，即使状态是 completed/failed，也不显示提示
          if (!isInitialLoad) {
            if (newStatus.status === 'completed') {
              // 检查是否是首次变为 completed 状态
              if (previousStatus !== 'completed') {
                message.success('批量分析完成')
                fetchData(pagination.current, pagination.pageSize)
              }
            } else if (newStatus.status === 'failed') {
              // 检查是否是首次变为 failed 状态
              if (previousStatus !== 'failed') {
                message.error('批量分析失败：' + (newStatus.error_message || '未知错误'))
              }
            }
          }
        }
        
        // 更新状态和上一次状态的引用
        setBatchAnalyzeStatus(newStatus)
        if (newStatus) {
          previousStatusRef.current = newStatus.status
        }
        
        // 首次加载完成后，标记为非首次加载
        if (isInitialLoad) {
          isInitialLoadRef.current = false
        }
      }
    } catch (error) {
      console.error('获取批量分析状态错误:', error)
    }
  }

  // 开始轮询批量分析状态
  const startAnalyzePolling = () => {
    // 清除之前的轮询
    if (analyzePollingInterval) {
      clearInterval(analyzePollingInterval)
    }
    // 每2秒轮询一次
    const interval = setInterval(() => {
      fetchBatchAnalyzeStatus()
    }, 2000)
    setAnalyzePollingInterval(interval)
  }

  // 停止轮询批量分析状态
  const stopAnalyzePolling = () => {
    if (analyzePollingInterval) {
      clearInterval(analyzePollingInterval)
      setAnalyzePollingInterval(null)
    }
  }

  // 组件卸载时清除轮询
  useEffect(() => {
    return () => {
      stopAnalyzePolling()
    }
  }, [])

  // 页面加载时获取批量分析状态
  useEffect(() => {
    fetchBatchAnalyzeStatus()
  }, [])

  // 当批量分析状态变化时，如果有运行中的任务，开始轮询
  useEffect(() => {
    if (batchAnalyzeStatus && batchAnalyzeStatus.status === 'running') {
      startAnalyzePolling()
    } else {
      stopAnalyzePolling()
    }
  }, [batchAnalyzeStatus])

  // 创建分类
  const handleCreateCategory = async () => {
    try {
      const values = await categoryForm.validateFields()
      const response = await api.post('/lut-categories', values)
      if (response.code === 200) {
        message.success('创建成功')
        setCategoryModalVisible(false)
        categoryForm.resetFields()
        fetchCategories()
      } else {
        message.error(response.message || '创建失败')
      }
    } catch (error) {
      if (error.errorFields) {
        return
      }
      message.error('创建失败：' + (error.response?.data?.message || error.message))
      console.error('创建错误:', error)
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
      key: 'thumbnail',
      width: 100,
      render: (_, record) => {
        if (record.thumbnail_path) {
          return (
            <Image
              src={`/api/lut-files/${record.id}/thumbnail`}
              alt={record.original_filename}
              width={80}
              height={80}
              style={{ objectFit: 'cover' }}
              preview={false}
            />
          )
        }
        return <span style={{ color: '#999' }}>无缩略图</span>
      }
    },
    {
      title: '分类',
      dataIndex: 'category_name',
      key: 'category_name',
      width: 120,
      render: (text) => text || <Tag color="default">未分类</Tag>
    },
    {
      title: '原始文件名',
      dataIndex: 'original_filename',
      key: 'original_filename',
      ellipsis: true
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
      title: '标签',
      key: 'tag',
      width: 200,
      render: (_, record) => {
        if (!record.tag) {
          return '-'
        }
        return (
          <Space direction="vertical" size="small">
            {record.tag.tone && (
              <Tag color="orange">色调: {record.tag.tone}</Tag>
            )}
            {record.tag.saturation && (
              <Tag color="cyan">饱和度: {record.tag.saturation}</Tag>
            )}
            {record.tag.contrast && (
              <Tag color="purple">对比度: {record.tag.contrast}</Tag>
            )}
          </Space>
        )
      }
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180
    },
    {
      title: '操作',
      key: 'action',
      width: 250,
      render: (_, record) => (
        <Space wrap>
          <Button
            type="link"
            size="small"
            icon={<ExperimentOutlined />}
            onClick={() => handleAnalyze(record.id)}
            disabled={!record.original_filename?.toLowerCase().endsWith('.cube')}
          >
            分析
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
          >
            编辑
          </Button>
          <Button
            type="link"
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => handleDownload(record.id, record.original_filename)}
          >
            下载
          </Button>
          <Popconfirm
            title="确定要删除这个文件吗？"
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
  ]

  return (
    <div>
      <Card
        title="Lut文件管理"
        extra={
          <Space>
            <Button
              type="primary"
              icon={<ExperimentOutlined />}
              onClick={() => handleBatchAnalyze(true, false)}
            >
              批量分析
            </Button>
            {(batchAnalyzeStatus && (batchAnalyzeStatus.status === 'failed' || batchAnalyzeStatus.status === 'completed')) && (
              <Button
                type="default"
                icon={<ExperimentOutlined />}
                onClick={handleRestartAnalyze}
              >
                重新分析
              </Button>
            )}
            <Button
              type="primary"
              icon={<FolderOutlined />}
              onClick={() => setCategoryModalVisible(true)}
            >
              分类管理
            </Button>
            <Button
              type="primary"
              icon={<UploadOutlined />}
              onClick={handleOpenUploadModal}
            >
              批量上传
            </Button>
          </Space>
        }
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          {/* 批量分析进度显示 */}
          {batchAnalyzeStatus && batchAnalyzeStatus.status === 'running' && (
            <Alert
              message={
                <div>
                  <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <strong>批量分析进行中...</strong>
                    <Button
                      type="link"
                      danger
                      size="small"
                      onClick={handleInterruptAnalyze}
                    >
                      中断任务
                    </Button>
                  </div>
                  <Progress
                    percent={
                      batchAnalyzeStatus.total_file_count > 0
                        ? Math.round((batchAnalyzeStatus.processed_file_count / batchAnalyzeStatus.total_file_count) * 100)
                        : 0
                    }
                    status="active"
                    format={(percent) => `${batchAnalyzeStatus.processed_file_count} / ${batchAnalyzeStatus.total_file_count}`}
                  />
                  <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                    成功: {batchAnalyzeStatus.success_count || 0}, 失败: {batchAnalyzeStatus.failed_count || 0}
                  </div>
                </div>
              }
              type="info"
              showIcon
              closable={false}
            />
          )}
          {batchAnalyzeStatus && batchAnalyzeStatus.status === 'completed' && (
            <Alert
              message={
                <div>
                  <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <strong>批量分析完成</strong>
                    <Button
                      type="link"
                      size="small"
                      icon={<ExperimentOutlined />}
                      onClick={handleRestartAnalyze}
                    >
                      重新分析
                    </Button>
                  </div>
                  <div style={{ fontSize: 12, color: '#666' }}>
                    成功: {batchAnalyzeStatus.success_count || 0}, 失败: {batchAnalyzeStatus.failed_count || 0}
                    {batchAnalyzeStatus.error_message && (
                      <div style={{ marginTop: 4, color: '#ff4d4f' }}>
                        {batchAnalyzeStatus.error_message}
                      </div>
                    )}
                  </div>
                </div>
              }
              type="success"
              showIcon
              closable
              onClose={() => setBatchAnalyzeStatus(null)}
            />
          )}
          {batchAnalyzeStatus && batchAnalyzeStatus.status === 'failed' && (
            <Alert
              message={
                <div>
                  <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <strong>批量分析失败</strong>
                    <Button
                      type="link"
                      size="small"
                      icon={<ExperimentOutlined />}
                      onClick={handleRestartAnalyze}
                    >
                      重新分析
                    </Button>
                  </div>
                  <div style={{ fontSize: 12, color: '#ff4d4f' }}>
                    {batchAnalyzeStatus.error_message || '未知错误'}
                  </div>
                </div>
              }
              type="error"
              showIcon
              closable
              onClose={() => setBatchAnalyzeStatus(null)}
            />
          )}
          <Space wrap>
            <Input
              placeholder="搜索文件名"
              value={filters.keyword}
              onChange={(e) => setFilters(prev => ({ ...prev, keyword: e.target.value }))}
              style={{ width: 200 }}
              allowClear
            />
            <Select
              placeholder="选择分类"
              value={filters.category_id}
              onChange={(value) => setFilters(prev => ({ ...prev, category_id: value }))}
              style={{ width: 200 }}
              allowClear
            >
              {categories.map(cat => (
                <Option key={cat.id} value={cat.id}>{cat.name}</Option>
              ))}
            </Select>
            <Select
              placeholder="色调"
              value={filters.tone}
              onChange={(value) => setFilters(prev => ({ ...prev, tone: value }))}
              style={{ width: 120 }}
              allowClear
            >
              <Option value="暖调">暖调</Option>
              <Option value="冷调">冷调</Option>
              <Option value="中性调">中性调</Option>
            </Select>
            <Select
              placeholder="饱和度"
              value={filters.saturation}
              onChange={(value) => setFilters(prev => ({ ...prev, saturation: value }))}
              style={{ width: 120 }}
              allowClear
            >
              <Option value="高饱和">高饱和</Option>
              <Option value="中饱和">中饱和</Option>
              <Option value="低饱和">低饱和</Option>
            </Select>
            <Select
              placeholder="对比度"
              value={filters.contrast}
              onChange={(value) => setFilters(prev => ({ ...prev, contrast: value }))}
              style={{ width: 120 }}
              allowClear
            >
              <Option value="高对比">高对比</Option>
              <Option value="中对比">中对比</Option>
              <Option value="低对比">低对比</Option>
            </Select>
            <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
              搜索
            </Button>
          </Space>

          <Table
            columns={columns}
            dataSource={dataSource}
            loading={loading}
            rowKey="id"
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

      {/* 编辑模态框 */}
      <Modal
        title="编辑Lut文件"
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="original_filename"
            label="原始文件名"
            rules={[{ required: true, message: '请输入原始文件名' }]}
          >
            <Input placeholder="输入原始文件名" />
          </Form.Item>
          <Form.Item
            name="category_id"
            label="分类"
          >
            <Select placeholder="选择分类" allowClear>
              {categories.map(cat => (
                <Option key={cat.id} value={cat.id}>{cat.name}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={4} placeholder="输入描述" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 上传模态框 */}
      <Modal
        title="批量上传Lut文件"
        open={uploadModalVisible}
        onOk={handleUpload}
        onCancel={() => {
          setUploadModalVisible(false)
          setUploadFileList([])
          setFilenameStartIndex(undefined)
        }}
        width={600}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Form.Item label="分类（可选）">
            <Select
              placeholder="选择分类"
              value={uploadCategoryId}
              onChange={setUploadCategoryId}
              style={{ width: '100%' }}
              allowClear
            >
              {categories.map(cat => (
                <Option key={cat.id} value={cat.id}>{cat.name}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item label="文件名截断起始位置（可选）">
            <Input
              type="number"
              placeholder="从第几个字符开始截取文件名（从0开始）"
              value={filenameStartIndex}
              onChange={(e) => {
                const value = e.target.value === '' ? undefined : e.target.value
                setFilenameStartIndex(value)
              }}
              min={0}
              style={{ width: '100%' }}
            />
            <div style={{ color: '#999', fontSize: 12, marginTop: 4 }}>
              例如：设置为5，则文件名"example_file.cube"会变成"le_file.cube"
            </div>
          </Form.Item>
          <Upload
            multiple
            fileList={uploadFileList}
            onChange={({ fileList }) => setUploadFileList(fileList)}
            beforeUpload={() => false}
            accept=".cube,.3dl,.csp,.look,.mga,.m3d"
          >
            <Button icon={<UploadOutlined />}>选择文件</Button>
          </Upload>
          <div style={{ color: '#999', fontSize: 12 }}>
            支持的文件格式：.cube, .3dl, .csp, .look, .mga, .m3d
          </div>
        </Space>
      </Modal>

      {/* 分类管理模态框 */}
      <Modal
        title="分类管理"
        open={categoryModalVisible}
        onOk={handleCreateCategory}
        onCancel={() => {
          setCategoryModalVisible(false)
          categoryForm.resetFields()
        }}
        footer={null}
        width={800}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Card title="创建新分类" size="small">
            <Form form={categoryForm} layout="inline" onFinish={handleCreateCategory}>
              <Form.Item
                name="name"
                label="分类名称"
                rules={[{ required: true, message: '请输入分类名称' }]}
              >
                <Input placeholder="输入分类名称" />
              </Form.Item>
              <Form.Item
                name="description"
                label="描述"
              >
                <Input placeholder="输入描述" />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit">创建</Button>
              </Form.Item>
            </Form>
          </Card>
          <Card title="分类列表" size="small">
            <Table
              columns={[
                { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
                { title: '名称', dataIndex: 'name', key: 'name' },
                { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
                {
                  title: '操作',
                  key: 'action',
                  width: 100,
                  render: (_, record) => (
                    <Popconfirm
                      title="确定要删除这个分类吗？"
                      onConfirm={async () => {
                        try {
                          const response = await api.delete(`/lut-categories/${record.id}`)
                          if (response.code === 200) {
                            message.success('删除成功')
                            fetchCategories()
                          } else {
                            message.error(response.message || '删除失败')
                          }
                        } catch (error) {
                          message.error('删除失败：' + (error.response?.data?.message || error.message))
                        }
                      }}
                    >
                      <Button type="link" danger size="small">删除</Button>
                    </Popconfirm>
                  )
                }
              ]}
              dataSource={categories}
              rowKey="id"
              pagination={false}
              size="small"
            />
          </Card>
        </Space>
      </Modal>
    </div>
  )
}

export default LutFileManagement

