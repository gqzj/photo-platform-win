import React, { useState } from 'react'
import { Card, Input, Button, Upload, Row, Col, Image, Spin, message, Empty, Space, Tag } from 'antd'
import { SearchOutlined, UploadOutlined, PictureOutlined, FileTextOutlined, DeleteOutlined } from '@ant-design/icons'
import api from '../services/api'
// 获取图片URL的工具函数
const getImageUrl = (image) => {
  // 优先使用storage_path，通过API接口获取图片内容
  if (image.storage_path) {
    return `/api/images/file/${image.id}/content`
  }
  // 如果没有storage_path，尝试使用original_url
  if (image.original_url) {
    return image.original_url
  }
  // 默认返回API接口
  return `/api/images/file/${image.id}/content`
}

const { TextArea } = Input

const SemanticSearch = () => {
  const [searchType, setSearchType] = useState('text') // 'text' 或 'image'
  const [textQuery, setTextQuery] = useState('')
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [topK, setTopK] = useState(100)

  // 文本搜索
  const handleTextSearch = async () => {
    if (!textQuery.trim()) {
      message.warning('请输入搜索关键词')
      return
    }

    setLoading(true)
    try {
      const response = await api.post('/semantic-search/search/text', {
        query: textQuery,
        top_k: topK
      })

      if (response.code === 200) {
        setResults(response.data.results || [])
        message.success(`找到 ${response.data.total} 个相似结果`)
      } else {
        message.error(response.message || '搜索失败')
        setResults([])
      }
    } catch (error) {
      message.error('搜索失败：' + (error.response?.data?.message || error.message))
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  // 图片搜索
  const handleImageSearch = async () => {
    if (!imageFile) {
      message.warning('请上传搜索图片')
      return
    }

    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('image', imageFile)
      formData.append('top_k', topK)

      const response = await api.post('/semantic-search/search/image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      if (response.code === 200) {
        setResults(response.data.results || [])
        message.success(`找到 ${response.data.total} 个相似结果`)
      } else {
        message.error(response.message || '搜索失败')
        setResults([])
      }
    } catch (error) {
      message.error('搜索失败：' + (error.response?.data?.message || error.message))
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  // 处理图片上传
  const handleImageUpload = (file) => {
    const isImage = file.type.startsWith('image/')
    if (!isImage) {
      message.error('只能上传图片文件')
      return false
    }

    const isLt10M = file.size / 1024 / 1024 < 10
    if (!isLt10M) {
      message.error('图片大小不能超过10MB')
      return false
    }

    setImageFile(file)
    
    // 预览图片
    const reader = new FileReader()
    reader.onload = (e) => {
      setImagePreview(e.target.result)
    }
    reader.readAsDataURL(file)

    return false // 阻止自动上传
  }

  // 移除上传的图片
  const handleRemoveImage = () => {
    setImageFile(null)
    setImagePreview(null)
  }

  // 删除图片（移动到回收站）
  const handleDeleteImage = async (imageId) => {
    try {
      const response = await api.post(`/semantic-search/images/${imageId}/recycle`)
      if (response.code === 200) {
        message.success('图片已移动到回收站')
        // 从结果列表中移除该图片
        setResults(results.filter(result => result.image_id !== imageId))
      } else {
        message.error(response.message || '删除失败')
      }
    } catch (error) {
      message.error('删除失败：' + (error.response?.data?.message || error.message))
    }
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card title="图片语义搜索" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 搜索类型选择 */}
          <Space>
            <Button
              type={searchType === 'text' ? 'primary' : 'default'}
              icon={<FileTextOutlined />}
              onClick={() => {
                setSearchType('text')
                setResults([])
              }}
            >
              文本搜索
            </Button>
            <Button
              type={searchType === 'image' ? 'primary' : 'default'}
              icon={<PictureOutlined />}
              onClick={() => {
                setSearchType('image')
                setResults([])
              }}
            >
              图片搜索
            </Button>
          </Space>

          {/* 文本搜索区域 */}
          {searchType === 'text' && (
            <Card size="small">
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <TextArea
                  placeholder="请输入搜索关键词，例如：一只在雪地里奔跑的金毛犬"
                  value={textQuery}
                  onChange={(e) => setTextQuery(e.target.value)}
                  rows={3}
                  onPressEnter={(e) => {
                    if (e.shiftKey) return
                    e.preventDefault()
                    handleTextSearch()
                  }}
                />
                <Space>
                  <Input
                    type="number"
                    placeholder="返回数量"
                    value={topK}
                    onChange={(e) => setTopK(parseInt(e.target.value) || 100)}
                    style={{ width: 120 }}
                    min={1}
                    max={1000}
                  />
                  <Button
                    type="primary"
                    icon={<SearchOutlined />}
                    onClick={handleTextSearch}
                    loading={loading}
                  >
                    搜索
                  </Button>
                </Space>
              </Space>
            </Card>
          )}

          {/* 图片搜索区域 */}
          {searchType === 'image' && (
            <Card size="small">
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <Upload
                  accept="image/*"
                  beforeUpload={handleImageUpload}
                  onRemove={handleRemoveImage}
                  maxCount={1}
                  showUploadList={false}
                >
                  <Button icon={<UploadOutlined />}>选择图片</Button>
                </Upload>
                
                {imagePreview && (
                  <div style={{ textAlign: 'center' }}>
                    <Image
                      src={imagePreview}
                      alt="预览"
                      style={{ maxWidth: '100%', maxHeight: 300 }}
                      preview={false}
                    />
                  </div>
                )}

                <Space>
                  <Input
                    type="number"
                    placeholder="返回数量"
                    value={topK}
                    onChange={(e) => setTopK(parseInt(e.target.value) || 100)}
                    style={{ width: 120 }}
                    min={1}
                    max={1000}
                  />
                  <Button
                    type="primary"
                    icon={<SearchOutlined />}
                    onClick={handleImageSearch}
                    loading={loading}
                    disabled={!imageFile}
                  >
                    搜索
                  </Button>
                </Space>
              </Space>
            </Card>
          )}
        </Space>
      </Card>

      {/* 搜索结果 */}
      <Card title={`搜索结果 (${results.length})`}>
        <Spin spinning={loading}>
          {results.length === 0 ? (
            <Empty description="暂无搜索结果" />
          ) : (
            <Row gutter={[16, 16]}>
              {results.map((result, index) => {
                const image = result.image
                const imageUrl = getImageUrl(image)
                
                return (
                  <Col key={result.image_id} xs={24} sm={12} md={8} lg={6} xl={4}>
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
                          justifyContent: 'center',
                          position: 'relative'
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
                          <div style={{
                            position: 'absolute',
                            top: 8,
                            right: 8,
                            zIndex: 10
                          }}>
                            <Button
                              type="primary"
                              danger
                              size="small"
                              icon={<DeleteOutlined />}
                              onClick={(e) => {
                                e.stopPropagation()
                                handleDeleteImage(result.image_id)
                              }}
                            />
                          </div>
                        </div>
                      }
                      bodyStyle={{ padding: 12 }}
                    >
                      <div style={{ marginBottom: 8 }}>
                        <Tag color="blue">相似度: {(result.score * 100).toFixed(2)}%</Tag>
                      </div>
                      <div style={{ fontSize: 12, color: '#666' }}>
                        ID: {image.id}
                      </div>
                    </Card>
                  </Col>
                )
              })}
            </Row>
          )}
        </Spin>
      </Card>
    </div>
  )
}

export default SemanticSearch
