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
  Checkbox
} from 'antd'
import { UploadOutlined, ReloadOutlined, TagOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Title, Text } = Typography
const { Option } = Select

const ImageTaggingTest = () => {
  const [fileList, setFileList] = useState([])
  const [loading, setLoading] = useState(false)
  const [taggingResult, setTaggingResult] = useState(null)
  const [imageUrl, setImageUrl] = useState('')
  const [features, setFeatures] = useState([])
  const [selectedFeatureIds, setSelectedFeatureIds] = useState([])

  // 获取特征列表
  const fetchFeatures = async () => {
    try {
      const response = await api.get('/features', { params: { page: 1, page_size: 1000, status: 'active' } })
      if (response.code === 200) {
        setFeatures(response.data.list || [])
      }
    } catch (error) {
      console.error('获取特征列表失败:', error)
      message.error('获取特征列表失败')
    }
  }

  useEffect(() => {
    fetchFeatures()
  }, [])

  // 上传配置
  const uploadProps = {
    beforeUpload: (file) => {
      // 检查文件类型
      const isImage = file.type.startsWith('image/')
      if (!isImage) {
        message.error('只能上传图片文件！')
        return false
      }
      
      // 检查文件大小（限制10MB）
      const isLt10M = file.size / 1024 / 1024 < 10
      if (!isLt10M) {
        message.error('图片大小不能超过10MB！')
        return false
      }
      
      // 读取文件预览
      const reader = new FileReader()
      reader.onload = (e) => {
        setImageUrl(e.target && e.target.result ? e.target.result : '')
      }
      reader.readAsDataURL(file)
      
      setFileList([file])
      return false // 阻止自动上传
    },
    fileList,
    onRemove: () => {
      setFileList([])
      setImageUrl('')
      setTaggingResult(null)
      setSelectedFeatureIds([])
    },
    maxCount: 1
  }

  // 执行打标
  const handleTag = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择图片文件')
      return
    }

    if (selectedFeatureIds.length === 0) {
      message.warning('请至少选择一个特征')
      return
    }

    setLoading(true)
    try {
      const file = fileList[0].originFileObj || fileList[0]
      const formData = new FormData()
      formData.append('file', file)
      formData.append('feature_ids', selectedFeatureIds.join(','))

      const response = await api.post('/image-tagging-test/tag', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      if (response.code === 200) {
        setTaggingResult(response.data)
        message.success('打标完成')
      } else {
        message.error(response.message || '打标失败')
      }
    } catch (error) {
      message.error('打标失败：' + (error.response?.data?.message || error.message))
      console.error('打标错误:', error)
    } finally {
      setLoading(false)
    }
  }

  // 重置
  const handleReset = () => {
    setFileList([])
    setImageUrl('')
    setTaggingResult(null)
    setSelectedFeatureIds([])
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Title level={4}>数据打标测试</Title>
        <Text type="secondary">上传图片并选择特征，使用大模型进行自动打标</Text>
        
        <div style={{ marginTop: 24 }}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {/* 上传区域 */}
            <Card size="small">
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <Upload {...uploadProps}>
                  <Button icon={<UploadOutlined />}>选择图片</Button>
                </Upload>
                
                {imageUrl && (
                  <div style={{ marginTop: 16 }}>
                    <Image
                      src={imageUrl}
                      alt="预览"
                      style={{ maxWidth: '100%', maxHeight: '400px' }}
                      preview={true}
                    />
                  </div>
                )}

                {/* 特征选择 */}
                <div style={{ width: '100%' }}>
                  <Text strong>选择要打标的特征（可多选）：</Text>
                  <div style={{ marginTop: 8 }}>
                    <Select
                      mode="multiple"
                      placeholder="请选择特征"
                      style={{ width: '100%' }}
                      value={selectedFeatureIds}
                      onChange={setSelectedFeatureIds}
                      showSearch
                      filterOption={(input, option) =>
                        (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                      }
                    >
                      {features.map(feature => (
                        <Option key={feature.id} value={feature.id} label={feature.name}>
                          <div>
                            <div>{feature.name}</div>
                            {feature.description && (
                              <Text type="secondary" style={{ fontSize: '12px' }}>
                                {feature.description}
                              </Text>
                            )}
                          </div>
                        </Option>
                      ))}
                    </Select>
                  </div>
                  {selectedFeatureIds.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <Space wrap>
                        {selectedFeatureIds.map(id => {
                          const feature = features.find(f => f.id === id)
                          return feature ? (
                            <Tag key={id} color={feature.color || 'blue'}>
                              {feature.name}
                            </Tag>
                          ) : null
                        })}
                      </Space>
                    </div>
                  )}
                </div>
                
                <Space>
                  <Button
                    type="primary"
                    icon={<TagOutlined />}
                    onClick={handleTag}
                    loading={loading}
                    disabled={fileList.length === 0 || selectedFeatureIds.length === 0}
                  >
                    开始打标
                  </Button>
                  <Button
                    icon={<ReloadOutlined />}
                    onClick={handleReset}
                    disabled={fileList.length === 0 && !taggingResult}
                  >
                    重置
                  </Button>
                </Space>
              </Space>
            </Card>

            {/* 打标结果 */}
            {loading && (
              <Card>
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <Spin size="large" />
                  <div style={{ marginTop: 16 }}>正在调用大模型进行打标...</div>
                </div>
              </Card>
            )}

            {taggingResult && !loading && (
              <Card title="打标结果">
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                  {/* 基本信息 */}
                  <Descriptions bordered column={2}>
                    <Descriptions.Item label="文件名">
                      {taggingResult.filename}
                    </Descriptions.Item>
                    <Descriptions.Item label="选择的特征">
                      {taggingResult.features?.length || 0} 个
                    </Descriptions.Item>
                  </Descriptions>

                  {/* 打标结果 */}
                  {taggingResult.tagging_result && (
                    <Card size="small" title="打标结果详情">
                      <Descriptions bordered column={1}>
                        {Object.entries(taggingResult.tagging_result).map(([key, value]) => {
                          // 跳过原始内容字段
                          if (key === 'raw_content' || key === 'error') {
                            return null
                          }
                          return (
                            <Descriptions.Item key={key} label={key}>
                              <Tag color="blue">{String(value)}</Tag>
                            </Descriptions.Item>
                          )
                        })}
                      </Descriptions>
                    </Card>
                  )}

                  {/* 原始响应 */}
                  {taggingResult.raw_response && (
                    <Card size="small" title="原始响应">
                      <pre style={{ 
                        background: '#f5f5f5', 
                        padding: '12px', 
                        borderRadius: '4px',
                        overflow: 'auto',
                        maxHeight: '300px'
                      }}>
                        {taggingResult.raw_response}
                      </pre>
                    </Card>
                  )}

                  {/* 错误信息 */}
                  {taggingResult.error && (
                    <Card size="small" title="错误信息" style={{ borderColor: '#ff4d4f' }}>
                      <Text type="danger">{taggingResult.error}</Text>
                    </Card>
                  )}
                </Space>
              </Card>
            )}
          </Space>
        </div>
      </Card>
    </div>
  )
}

export default ImageTaggingTest

