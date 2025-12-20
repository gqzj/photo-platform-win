import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Tag
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, PlayCircleOutlined, ReloadOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Option } = Select
const { TextArea } = Input

const CrawlerTask = () => {
  const [dataSource, setDataSource] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  })
  const [modalVisible, setModalVisible] = useState(false)
  const [editingRecord, setEditingRecord] = useState(null)
  const [form] = Form.useForm()
  const [cookieOptions, setCookieOptions] = useState([])

  // 获取列表数据
  const fetchData = async (page = 1, pageSize = 10) => {
    setLoading(true)
    try {
      const response = await api.get('/crawler/tasks', {
        params: { page, page_size: pageSize }
      })
      if (response.code === 200) {
        setDataSource(response.data.list)
        setPagination({
          current: response.data.page,
          pageSize: response.data.page_size,
          total: response.data.total
        })
      } else {
        message.error(response.message || '获取数据失败')
      }
    } catch (error) {
      const errorMsg = error.response?.data?.message || error.message || '未知错误'
      message.error('获取数据失败：' + errorMsg)
      console.error('API Error:', error.response?.data || error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  // 获取Cookie列表（根据平台筛选）
  const fetchCookies = async (platform) => {
    if (!platform) {
      setCookieOptions([])
      return
    }
    try {
      const response = await api.get('/crawler/cookies', {
        params: { page: 1, page_size: 1000, platform, status: 'active' }
      })
      if (response.code === 200) {
        const cookies = response.data.list || []
        setCookieOptions(cookies.map(cookie => ({
          value: cookie.id,
          label: cookie.platform_account || `Cookie #${cookie.id}`,
          cookie: cookie
        })))
      }
    } catch (error) {
      console.error('获取Cookie列表失败:', error)
      setCookieOptions([])
    }
  }

  // 打开新增/编辑弹窗
  const handleOpenModal = (record = null) => {
    setEditingRecord(record)
    if (record) {
      form.resetFields()
      // 处理keywords_json，转换为数组格式用于显示
      let keywords = []
      if (record.keywords_json) {
        try {
          const parsed = JSON.parse(record.keywords_json)
          keywords = Array.isArray(parsed) ? parsed : []
        } catch {
          keywords = []
        }
      }
      
      // 先设置基础字段
      form.setFieldsValue({
        name: record.name,
        platform: record.platform,
        task_type: record.task_type,
        cookie_id: record.cookie_id,
        note: record.note
      })
      
      // 加载该平台的Cookie列表
      if (record.platform) {
        fetchCookies(record.platform)
      }
      
      // 延迟设置动态字段
      setTimeout(() => {
        if (record.task_type === 'keyword') {
          form.setFieldsValue({
            keywords: keywords
          })
        } else if (record.task_type === 'url') {
          form.setFieldsValue({
            target_url: record.target_url
          })
        }
      }, 100)
    } else {
      form.resetFields()
      form.setFieldsValue({
        task_type: 'keyword',
        platform: 'xiaohongshu'
      })
      // 新增任务时，加载默认平台的Cookie列表
      fetchCookies('xiaohongshu')
    }
    setModalVisible(true)
  }

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const submitData = { ...values }
      
      // 处理关键字：如果是关键字类型，将关键字数组转换为JSON
      if (submitData.task_type === 'keyword') {
        if (submitData.keywords && submitData.keywords.length > 0) {
          submitData.keywords_json = JSON.stringify(submitData.keywords.filter(k => k && k.trim()))
        }
        delete submitData.keywords
        delete submitData.target_url
      } else if (submitData.task_type === 'url') {
        // URL类型：清除keywords_json
        delete submitData.keywords
        delete submitData.keywords_json
      }

      if (editingRecord) {
        // 更新
        const response = await api.put(`/crawler/tasks/${editingRecord.id}`, submitData)
        if (response.code === 200) {
          message.success('更新成功')
          setModalVisible(false)
          fetchData(pagination.current, pagination.pageSize)
        } else {
          message.error(response.message || '更新失败')
        }
      } else {
        // 新增
        const response = await api.post('/crawler/tasks', submitData)
        if (response.code === 200) {
          message.success('创建成功')
          setModalVisible(false)
          fetchData(pagination.current, pagination.pageSize)
        } else {
          message.error(response.message || '创建失败')
        }
      }
    } catch (error) {
      if (error.errorFields) {
        return // 表单验证错误
      }
      message.error('操作失败：' + (error.message || '未知错误'))
    }
  }

  // 刷新任务
  const handleRefresh = async (record) => {
    try {
      const response = await api.post(`/crawler/tasks/${record.id}/refresh`)
      if (response.code === 200) {
        message.success('刷新成功')
        // 刷新列表数据
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error(response.message || '刷新失败')
      }
    } catch (error) {
      const errorMsg = error.response?.data?.message || error.message || '未知错误'
      message.error('刷新失败：' + errorMsg)
      console.error('刷新任务错误:', error)
    }
  }

  // 删除
  const handleDelete = async (id) => {
    try {
      const response = await api.delete(`/crawler/tasks/${id}`)
      if (response.code === 200) {
        message.success('删除成功')
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error(response.message || '删除失败')
      }
    } catch (error) {
      message.error('删除失败：' + (error.message || '未知错误'))
    }
  }

  // 执行抓取
  const handleCrawl = async (record) => {
    console.log('开始抓取任务:', record)
    try {
      message.loading({ content: '正在抓取中，请稍候...', key: 'crawl', duration: 0 })
      const response = await api.post(`/crawler/tasks/${record.id}/crawl`)
      message.destroy('crawl')
      
      console.log('抓取响应:', response)
      
      if (response.code === 200) {
        const stats = response.data?.stats || {}
        message.success(
          `抓取完成！帖子: ${stats.posts || 0}, 评论: ${stats.comments || 0}, 媒体: ${stats.media || 0}, 图片: ${stats.images || 0}`
        )
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error(response.message || '抓取失败')
      }
    } catch (error) {
      message.destroy('crawl')
      const errorMsg = error.response?.data?.message || error.message || '未知错误'
      message.error('抓取失败：' + errorMsg)
      console.error('抓取错误详情:', error)
      if (error.response) {
        console.error('响应数据:', error.response.data)
      }
    }
  }

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80
    },
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      width: 150
    },
    {
      title: '平台',
      dataIndex: 'platform',
      key: 'platform',
      width: 120
    },
    {
      title: '抓取账号',
      dataIndex: 'cookie_id',
      key: 'cookie_id',
      width: 150,
      render: (cookieId, record) => {
        if (!cookieId) {
          return <span style={{ color: '#999' }}>使用默认账号</span>
        }
        // 这里可以显示账号信息，但需要从cookie列表中查找
        return <span>账号 #{cookieId}</span>
      }
    },
    {
      title: '任务类型',
      dataIndex: 'task_type',
      key: 'task_type',
      width: 120,
      render: (type) => {
        const textMap = {
          'keyword': '关键字爬取',
          'url': '目标URL'
        }
        return textMap[type] || type
      }
    },
    {
      title: '目标/关键字',
      key: 'target',
      width: 250,
      ellipsis: true,
      render: (_, record) => {
        if (record.task_type === 'keyword' && record.keywords_json) {
          try {
            const keywords = JSON.parse(record.keywords_json)
            if (Array.isArray(keywords) && keywords.length > 0) {
              return keywords.join(', ')
            }
          } catch {
            return record.keywords_json
          }
        }
        return record.target_url || '-'
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const colorMap = {
          'pending': 'default',
          'running': 'processing',
          'paused': 'warning',
          'completed': 'success',
          'failed': 'error'
        }
        const textMap = {
          'pending': '待执行',
          'running': '运行中',
          'paused': '已暂停',
          'completed': '已完成',
          'failed': '失败'
        }
        return <Tag color={colorMap[status] || 'default'}>{textMap[status] || status}</Tag>
      }
    },
    {
      title: '进度',
      key: 'progress',
      width: 150,
      render: (_, record) => {
        const total = record.processed_posts + record.processed_comments + record.downloaded_media
        return total > 0 ? (
          <span>
            帖子: {record.processed_posts} | 
            评论: {record.processed_comments} | 
            媒体: {record.downloaded_media}
          </span>
        ) : '-'
      }
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180
    },
    {
      title: '操作',
      key: 'action',
      width: 300,
      fixed: 'right',
      render: (_, record) => {
        // 显示抓取按钮的条件：关键字类型，且状态不是running（或者running状态但可以重新运行）
        const showCrawlButton = record.task_type === 'keyword' && record.status !== 'running'
        return (
          <Space>
            {showCrawlButton && (
              <Button
                type="link"
                size="small"
                icon={<PlayCircleOutlined />}
                onClick={() => {
                  console.log('点击抓取按钮，任务信息:', record)
                  handleCrawl(record)
                }}
              >
                抓取
              </Button>
            )}
            {record.task_type === 'keyword' && record.status === 'running' && (
              <Button
                type="link"
                size="small"
                icon={<PlayCircleOutlined />}
                onClick={() => {
                  console.log('任务正在运行中，尝试重新运行:', record)
                  handleCrawl(record)
                }}
                disabled
                title="任务正在运行中"
              >
                运行中
              </Button>
            )}
          <Button
            type="link"
            size="small"
            icon={<ReloadOutlined />}
            onClick={() => handleRefresh(record)}
            title="刷新任务状态和统计数据"
          >
            刷新
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这条记录吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              danger
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
        title="任务管理"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleOpenModal()}
          >
            新增任务
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={dataSource}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => {
              fetchData(page, pageSize)
            },
            onShowSizeChange: (current, size) => {
              fetchData(current, size)
            }
          }}
          scroll={{ x: 1400 }}
        />
      </Card>

      <Modal
        title={editingRecord ? '编辑任务' : '新增任务'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
        }}
        width={800}
        okText="确定"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            task_type: 'keyword',
            platform: 'xiaohongshu'
          }}
        >
          <Form.Item
            name="name"
            label="任务名称"
            rules={[{ required: true, message: '请输入任务名称' }]}
          >
            <Input placeholder="请输入任务名称" />
          </Form.Item>

          <Form.Item
            name="platform"
            label="平台"
            rules={[{ required: true, message: '请选择平台' }]}
          >
            <Select 
              placeholder="请选择平台"
              onChange={(value) => {
                // 平台改变时，加载该平台的Cookie列表
                fetchCookies(value)
                // 清空cookie_id选择
                form.setFieldsValue({ cookie_id: undefined })
              }}
            >
              <Option value="xiaohongshu">小红书</Option>
              <Option value="douyin">抖音</Option>
              <Option value="weibo">微博</Option>
              <Option value="other">其他</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="cookie_id"
            label="抓取账号"
            tooltip="选择用于抓取的账号Cookie，如果不选择则使用该平台默认的active状态Cookie"
          >
            <Select 
              placeholder="请选择账号（可选）"
              allowClear
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
            >
              {cookieOptions.map(option => (
                <Option key={option.value} value={option.value}>
                  {option.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="task_type"
            label="任务类型"
            rules={[{ required: true, message: '请选择任务类型' }]}
          >
            <Select placeholder="请选择任务类型">
              <Option value="keyword">关键字爬取</Option>
              <Option value="url">目标URL</Option>
            </Select>
          </Form.Item>

          {/* 关键字爬取类型：显示关键字输入 */}
          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues.task_type !== currentValues.task_type
            }
          >
            {({ getFieldValue }) => {
              const taskType = getFieldValue('task_type')
              if (taskType === 'keyword') {
                return (
                  <Form.Item
                    name="keywords"
                    label="关键字"
                    rules={[
                      { required: true, message: '请输入至少一个关键字' },
                      {
                        validator: (_, value) => {
                          if (!value || value.length === 0) {
                            return Promise.reject(new Error('请输入至少一个关键字'))
                          }
                          const validKeywords = value.filter(k => k && k.trim())
                          if (validKeywords.length === 0) {
                            return Promise.reject(new Error('请输入至少一个有效关键字'))
                          }
                          return Promise.resolve()
                        }
                      }
                    ]}
                  >
                    <Select
                      mode="tags"
                      placeholder="请输入关键字，按回车或逗号添加多个"
                      tokenSeparators={[',', '，']}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                )
              }
              return null
            }}
          </Form.Item>

          {/* 目标URL类型：显示URL输入 */}
          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues.task_type !== currentValues.task_type
            }
          >
            {({ getFieldValue }) => {
              const taskType = getFieldValue('task_type')
              if (taskType === 'url') {
                return (
                  <Form.Item
                    name="target_url"
                    label="目标URL"
                    rules={[{ required: true, message: '请输入目标URL' }]}
                  >
                    <Input placeholder="请输入目标URL" />
                  </Form.Item>
                )
              }
              return null
            }}
          </Form.Item>

          <Form.Item
            name="note"
            label="备注"
          >
            <TextArea
              rows={3}
              placeholder="请输入备注（可选）"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default CrawlerTask
