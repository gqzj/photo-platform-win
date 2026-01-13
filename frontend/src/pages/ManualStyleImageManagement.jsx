import React, { useState, useEffect } from 'react'
import {
  Card,
  Button,
  Space,
  Input,
  message,
  Popconfirm,
  Tag,
  Row,
  Col,
  Image,
  Checkbox,
  Modal,
  Statistic,
  Divider,
  Empty,
  Pagination,
  Spin
} from 'antd'
import {
  SearchOutlined,
  DeleteOutlined,
  ReloadOutlined,
  PlusOutlined,
  FileSearchOutlined,
  UploadOutlined,
  PictureOutlined,
  FileTextOutlined
} from '@ant-design/icons'
import { Upload } from 'antd'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../services/api'

const { TextArea } = Input

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

const ManualStyleImageManagement = () => {
  const { styleId } = useParams()
  const navigate = useNavigate()
  const [style, setStyle] = useState(null)
  const [imageList, setImageList] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  })
  
  // 语义搜索相关
  const [searchType, setSearchType] = useState('text') // 'text' 或 'image'
  const [searchQuery, setSearchQuery] = useState('')
  const [searchImageFile, setSearchImageFile] = useState(null)
  const [searchImagePreview, setSearchImagePreview] = useState(null)
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchResults, setSearchResults] = useState([])
  const [selectedImageIds, setSelectedImageIds] = useState([])
  const [addModalVisible, setAddModalVisible] = useState(false)

  // 获取风格信息
  const fetchStyle = async () => {
    try {
      const response = await api.get(`/manual-styles/${styleId}/images`, {
        params: { page: 1, page_size: 1 }
      })
      if (response.code === 200) {
        setStyle(response.data.style)
      }
    } catch (error) {
      message.error('获取风格信息失败：' + (error.response?.data?.message || error.message))
    }
  }

  // 获取图片列表
  const fetchImageList = async (page = 1, pageSize = 20) => {
    setLoading(true)
    try {
      const response = await api.get(`/manual-styles/${styleId}/images`, {
        params: { page, page_size: pageSize }
      })
      if (response.code === 200) {
        setImageList(response.data.list)
        setPagination({
          current: response.data.page,
          pageSize: response.data.page_size,
          total: response.data.total
        })
        if (response.data.style) {
          setStyle(response.data.style)
        }
      } else {
        message.error(response.message || '获取图片列表失败')
      }
    } catch (error) {
      message.error('获取图片列表失败：' + (error.response?.data?.message || error.message))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (styleId) {
      fetchStyle()
      fetchImageList(pagination.current, pagination.pageSize)
    }
  }, [styleId])

  // 文本搜索
  const handleTextSearch = async () => {
    if (!searchQuery.trim()) {
      message.warning('请输入搜索关键词')
      return
    }

    setSearchLoading(true)
    setSearchResults([])
    setSelectedImageIds([])
    
    try {
      const response = await api.post(`/manual-styles/${styleId}/images/search`, {
        query: searchQuery,
        top_k: 50
      })
      
      if (response.code === 200) {
        setSearchResults(response.data.results || [])
        setAddModalVisible(true)
        if (response.data.results.length === 0) {
          message.info('未找到相关图片')
        }
      } else {
        message.error(response.message || '搜索失败')
      }
    } catch (error) {
      message.error('搜索失败：' + (error.response?.data?.message || error.message))
    } finally {
      setSearchLoading(false)
    }
  }

  // 图片搜索
  const handleImageSearch = async () => {
    if (!searchImageFile) {
      message.warning('请上传搜索图片')
      return
    }

    setSearchLoading(true)
    setSearchResults([])
    setSelectedImageIds([])
    
    try {
      const formData = new FormData()
      formData.append('image', searchImageFile)
      formData.append('top_k', 50)

      const response = await api.post(`/manual-styles/${styleId}/images/search`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      if (response.code === 200) {
        setSearchResults(response.data.results || [])
        setAddModalVisible(true)
        if (response.data.results.length === 0) {
          message.info('未找到相关图片')
        }
      } else {
        message.error(response.message || '搜索失败')
      }
    } catch (error) {
      message.error('搜索失败：' + (error.response?.data?.message || error.message))
    } finally {
      setSearchLoading(false)
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

    setSearchImageFile(file)
    
    // 预览图片
    const reader = new FileReader()
    reader.onload = (e) => {
      setSearchImagePreview(e.target.result)
    }
    reader.readAsDataURL(file)

    return false // 阻止自动上传
  }

  // 移除上传的图片
  const handleRemoveImage = () => {
    setSearchImageFile(null)
    setSearchImagePreview(null)
  }

  // 选择/取消选择图片
  const handleToggleSelect = (imageId) => {
    setSelectedImageIds(prev => {
      if (prev.includes(imageId)) {
        return prev.filter(id => id !== imageId)
      } else {
        return [...prev, imageId]
      }
    })
  }

  // 全选/取消全选
  const handleSelectAll = (checked) => {
    if (checked) {
      const availableIds = searchResults
        .filter(r => !r.already_added)
        .map(r => r.image_id)
      setSelectedImageIds(availableIds)
    } else {
      setSelectedImageIds([])
    }
  }

  // 添加选中的图片到风格
  const handleAddImages = async () => {
    if (selectedImageIds.length === 0) {
      message.warning('请选择要添加的图片')
      return
    }

    try {
      const response = await api.post(`/manual-styles/${styleId}/images`, {
        image_ids: selectedImageIds
      })
      
      if (response.code === 200) {
        message.success(`成功添加 ${response.data.added_count} 张图片`)
        setAddModalVisible(false)
        setSearchResults([])
        setSelectedImageIds([])
        setSearchQuery('')
        setSearchImageFile(null)
        setSearchImagePreview(null)
        fetchImageList(pagination.current, pagination.pageSize)
        fetchStyle()
      } else {
        message.error(response.message || '添加失败')
      }
    } catch (error) {
      message.error('添加失败：' + (error.response?.data?.message || error.message))
    }
  }

  // 删除图片
  const handleDeleteImage = async (imageId) => {
    try {
      const response = await api.delete(`/manual-styles/${styleId}/images/${imageId}`)
      if (response.code === 200) {
        message.success('删除成功')
        fetchImageList(pagination.current, pagination.pageSize)
        fetchStyle()
      } else {
        message.error(response.message || '删除失败')
      }
    } catch (error) {
      message.error('删除失败：' + (error.response?.data?.message || error.message))
    }
  }

  // 提取LUT
  const handleExtractLut = async () => {
    try {
      message.loading({ content: '正在提取LUT，请稍候...', key: 'extractLut', duration: 0 })
      const response = await api.post(`/manual-styles/${styleId}/extract-lut`)
      if (response.code === 200) {
        const data = response.data
        if (data.lut_file_id) {
          const categoryName = data.category_name || '手工风格定义'
          message.success({
            content: `LUT提取成功！文件：${data.lut_file_name}，已保存到"${categoryName}"分类，文件ID: ${data.lut_file_id}`,
            key: 'extractLut',
            duration: 5
          })
          // 刷新页面数据
          fetchStyle()
        } else {
          message.info({
            content: response.message || 'LUT提取完成',
            key: 'extractLut',
            duration: 3
          })
        }
      } else {
        message.error({
          content: response.message || '提取失败',
          key: 'extractLut',
          duration: 3
        })
      }
    } catch (error) {
      message.error({
        content: '提取失败：' + (error.response?.data?.message || error.message),
        key: 'extractLut',
        duration: 5
      })
    }
  }


  const availableResults = searchResults.filter(r => !r.already_added)
  const allSelected = availableResults.length > 0 && 
    availableResults.every(r => selectedImageIds.includes(r.image_id))

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <Space>
            <Button onClick={() => navigate('/style/manual')}>返回</Button>
            <span>{style?.name || '手工风格图片管理'}</span>
          </Space>
        }
        extra={
          <Space>
            <Button
              type="primary"
              icon={<FileSearchOutlined />}
              onClick={() => setAddModalVisible(true)}
            >
              语义搜索添加图片
            </Button>
            <Button
              type="default"
              onClick={handleExtractLut}
              disabled={!style || style.image_count === 0}
            >
              提取LUT
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                fetchImageList(pagination.current, pagination.pageSize)
                fetchStyle()
              }}
            >
              刷新
            </Button>
          </Space>
        }
      >
        {style && (
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={6}>
              <Statistic title="风格名称" value={style.name} />
            </Col>
            <Col span={6}>
              <Statistic title="图片数量" value={style.image_count} />
            </Col>
            <Col span={6}>
              <Statistic title="状态" value={style.status === 'active' ? '启用' : '禁用'} />
            </Col>
            <Col span={6}>
              <Statistic title="创建时间" value={style.created_at} />
            </Col>
          </Row>
        )}

        {style?.description && (
          <div style={{ marginBottom: 16 }}>
            <strong>描述：</strong>{style.description}
          </div>
        )}

        <Divider />

        <Spin spinning={loading}>
          {imageList.length === 0 ? (
            <Empty description="暂无图片" />
          ) : (
            <>
              <Row gutter={[16, 16]}>
                {imageList.map((record) => {
                  const image = record.image
                  if (!image) return null
                  
                  return (
                    <Col key={record.id} xs={12} sm={8} md={6} lg={4} xl={4}>
                      <Card
                        hoverable
                        style={{ height: '100%' }}
                        cover={
                          <Image
                            src={getImageUrl(image)}
                            alt={image.id}
                            height={200}
                            style={{ objectFit: 'cover' }}
                            preview={{
                              src: getImageUrl(image)
                            }}
                          />
                        }
                        actions={[
                          <Popconfirm
                            key="delete"
                            title="确定要从风格中删除这张图片吗？"
                            onConfirm={() => handleDeleteImage(record.image_id)}
                            okText="确定"
                            cancelText="取消"
                          >
                            <Button
                              type="text"
                              danger
                              icon={<DeleteOutlined />}
                              size="small"
                            >
                              删除
                            </Button>
                          </Popconfirm>
                        ]}
                      >
                        <Card.Meta
                          title={`ID: ${image.id}`}
                          description={
                            <div style={{ fontSize: '12px', color: '#999' }}>
                              {record.created_at}
                            </div>
                          }
                        />
                      </Card>
                    </Col>
                  )
                })}
              </Row>
              
              <div style={{ marginTop: 24, textAlign: 'right' }}>
                <Pagination
                  current={pagination.current}
                  pageSize={pagination.pageSize}
                  total={pagination.total}
                  showSizeChanger
                  showTotal={(total) => `共 ${total} 张图片`}
                  pageSizeOptions={['12', '24', '48', '96']}
                  onChange={(page, pageSize) => {
                    setPagination({ ...pagination, current: page, pageSize })
                    fetchImageList(page, pageSize)
                  }}
                  onShowSizeChange={(current, size) => {
                    setPagination({ ...pagination, current: 1, pageSize: size })
                    fetchImageList(1, size)
                  }}
                />
              </div>
            </>
          )}
        </Spin>
      </Card>

      {/* 语义搜索添加图片弹窗 */}
      <Modal
        title="语义搜索添加图片"
        open={addModalVisible}
        onCancel={() => {
          setAddModalVisible(false)
          setSearchResults([])
          setSelectedImageIds([])
          setSearchQuery('')
          setSearchImageFile(null)
          setSearchImagePreview(null)
        }}
        width={1200}
        footer={[
          <Button key="cancel" onClick={() => {
            setAddModalVisible(false)
            setSearchResults([])
            setSelectedImageIds([])
            setSearchQuery('')
            setSearchImageFile(null)
            setSearchImagePreview(null)
          }}>
            取消
          </Button>,
          <Button
            key="selectAll"
            onClick={() => handleSelectAll(!allSelected)}
            disabled={availableResults.length === 0}
          >
            {allSelected ? '取消全选' : '全选'}
          </Button>,
          <Button
            key="add"
            type="primary"
            onClick={handleAddImages}
            disabled={selectedImageIds.length === 0}
          >
            添加选中图片 ({selectedImageIds.length})
          </Button>
        ]}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 搜索类型选择 */}
          <Space>
            <Button
              type={searchType === 'text' ? 'primary' : 'default'}
              icon={<FileTextOutlined />}
              onClick={() => {
                setSearchType('text')
                setSearchResults([])
                setSelectedImageIds([])
              }}
            >
              文本搜索
            </Button>
            <Button
              type={searchType === 'image' ? 'primary' : 'default'}
              icon={<PictureOutlined />}
              onClick={() => {
                setSearchType('image')
                setSearchResults([])
                setSelectedImageIds([])
              }}
            >
              图片搜索
            </Button>
          </Space>

          {/* 文本搜索 */}
          {searchType === 'text' && (
            <Input.Search
              placeholder="输入搜索关键词，例如：温暖的色调、复古风格、清新自然等"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onSearch={handleTextSearch}
              enterButton={<SearchOutlined />}
              loading={searchLoading}
              size="large"
            />
          )}

          {/* 图片搜索 */}
          {searchType === 'image' && (
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <Upload
                accept="image/*"
                beforeUpload={handleImageUpload}
                onRemove={handleRemoveImage}
                maxCount={1}
                showUploadList={false}
              >
                <Button icon={<UploadOutlined />}>
                  上传搜索图片
                </Button>
              </Upload>
              {searchImagePreview && (
                <div>
                  <Image
                    src={searchImagePreview}
                    alt="预览"
                    width={200}
                    height={200}
                    style={{ objectFit: 'cover' }}
                  />
                  <div style={{ marginTop: 8 }}>
                    <Button
                      type="primary"
                      icon={<SearchOutlined />}
                      onClick={handleImageSearch}
                      loading={searchLoading}
                    >
                      开始搜索
                    </Button>
                    <Button
                      style={{ marginLeft: 8 }}
                      onClick={handleRemoveImage}
                    >
                      移除图片
                    </Button>
                  </div>
                </div>
              )}
            </Space>
          )}

          {searchResults.length > 0 && (
            <div>
              <div style={{ marginBottom: 16 }}>
                找到 {searchResults.length} 个结果，已选择 {selectedImageIds.length} 张
              </div>
              <Row gutter={[16, 16]}>
                {searchResults.map((result) => {
                  const image = result.image
                  const isSelected = selectedImageIds.includes(result.image_id)
                  const isAlreadyAdded = result.already_added
                  
                  return (
                    <Col key={result.image_id} span={6}>
                      <Card
                        hoverable
                        style={{
                          border: isSelected ? '2px solid #1890ff' : '1px solid #d9d9d9',
                          opacity: isAlreadyAdded ? 0.6 : 1
                        }}
                        cover={
                          <div style={{ position: 'relative', height: 200, overflow: 'hidden' }}>
                            <Image
                              src={getImageUrl(image)}
                              alt={image.id}
                              width="100%"
                              height={200}
                              style={{ objectFit: 'cover' }}
                              preview={{
                                src: getImageUrl(image)
                              }}
                            />
                            {isAlreadyAdded && (
                              <div
                                style={{
                                  position: 'absolute',
                                  top: 0,
                                  left: 0,
                                  right: 0,
                                  bottom: 0,
                                  background: 'rgba(0,0,0,0.5)',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  color: '#fff',
                                  fontWeight: 'bold'
                                }}
                              >
                                已添加
                              </div>
                            )}
                          </div>
                        }
                        onClick={() => {
                          if (!isAlreadyAdded) {
                            handleToggleSelect(result.image_id)
                          }
                        }}
                      >
                        <div style={{ padding: '8px 0' }}>
                          <div>ID: {image.id}</div>
                          <div style={{ fontSize: 12, color: '#666' }}>
                            相似度: {(result.score * 100).toFixed(1)}%
                          </div>
                          {!isAlreadyAdded && (
                            <Checkbox
                              checked={isSelected}
                              onChange={(e) => {
                                e.stopPropagation()
                                handleToggleSelect(result.image_id)
                              }}
                              style={{ marginTop: 8 }}
                            >
                              选择
                            </Checkbox>
                          )}
                        </div>
                      </Card>
                    </Col>
                  )
                })}
              </Row>
            </div>
          )}

          {searchResults.length === 0 && !searchLoading && (
            <Empty description={searchType === 'text' ? '请输入关键词进行搜索' : '请上传图片进行搜索'} />
          )}
        </Space>
      </Modal>
    </div>
  )
}

export default ManualStyleImageManagement
