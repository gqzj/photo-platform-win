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
  Empty,
  Pagination,
  Spin
} from 'antd'
import {
  SearchOutlined,
  DeleteOutlined,
  ArrowLeftOutlined,
  PlusOutlined
} from '@ant-design/icons'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../services/api'

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

const FeatureStyleSubStyleImageManagement = () => {
  const { definitionId, subStyleId } = useParams()
  const navigate = useNavigate()
  const [subStyle, setSubStyle] = useState(null)
  const [imageList, setImageList] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  })

  // 获取子风格信息
  const fetchSubStyle = async () => {
    try {
      const response = await api.get(`/feature-style-definitions/${definitionId}/sub-styles`)
      if (response.code === 200) {
        const subStyle = response.data.list.find(s => s.id === parseInt(subStyleId))
        if (subStyle) {
          setSubStyle(subStyle)
        }
      }
    } catch (error) {
      message.error('获取子风格信息失败：' + (error.response?.data?.message || error.message))
    }
  }

  // 获取图片列表
  const fetchImageList = async (page = 1, pageSize = 20) => {
    setLoading(true)
    try {
      const response = await api.get(`/feature-style-definitions/sub-styles/${subStyleId}/images`, {
        params: { page, page_size: pageSize }
      })
      if (response.code === 200) {
        setImageList(response.data.list)
        setPagination({
          current: response.data.page,
          pageSize: response.data.page_size,
          total: response.data.total
        })
        if (response.data.sub_style_name && !subStyle) {
          setSubStyle({ name: response.data.sub_style_name })
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
    fetchSubStyle()
    fetchImageList(pagination.current, pagination.pageSize)
  }, [subStyleId])

  // 删除图片
  const handleDeleteImage = async (imageId) => {
    try {
      const response = await api.delete(`/feature-style-definitions/sub-styles/${subStyleId}/images/${imageId}`)
      if (response.code === 200) {
        message.success('删除成功')
        fetchImageList(pagination.current, pagination.pageSize)
        fetchSubStyle()
      } else {
        message.error(response.message || '删除失败')
      }
    } catch (error) {
      message.error('删除失败：' + (error.response?.data?.message || error.message))
    }
  }

  return (
    <div>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 标题和返回 */}
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(`/style/feature-style-definition/${definitionId}/sub-styles`)}>
              返回
            </Button>
            <h2 style={{ margin: 0 }}>
              {subStyle?.name || '子风格'} - 图片列表
            </h2>
          </Space>

          {/* 子风格信息 */}
          {subStyle && (
            <Card size="small">
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <div><strong>子风格名称：</strong>{subStyle.name}</div>
                {subStyle.dimension_values && (
                  <div>
                    <strong>维度值组合：</strong>
                    {Object.entries(subStyle.dimension_values).map(([key, value]) => (
                      <Tag key={key} style={{ marginRight: 8 }}>
                        {key}: {value}
                      </Tag>
                    ))}
                  </div>
                )}
                <div><strong>图片数量：</strong>{subStyle.image_count || 0}</div>
              </Space>
            </Card>
          )}

          {/* 图片列表 */}
          <Spin spinning={loading}>
            {imageList.length > 0 ? (
              <>
                <Row gutter={[16, 16]}>
                  {imageList.map((item) => (
                    <Col key={item.id} xs={12} sm={8} md={6} lg={4} xl={3}>
                      <Card
                        hoverable
                        cover={
                          <Image
                            src={getImageUrl(item.image)}
                            alt={item.image?.filename}
                            style={{ height: 200, objectFit: 'cover' }}
                            preview={{
                              mask: '预览'
                            }}
                          />
                        }
                        actions={[
                          <Popconfirm
                            key="delete"
                            title="确定要删除吗？"
                            onConfirm={() => handleDeleteImage(item.image_id)}
                            okText="确定"
                            cancelText="取消"
                          >
                            <Button type="link" danger icon={<DeleteOutlined />} size="small">
                              删除
                            </Button>
                          </Popconfirm>
                        ]}
                      >
                        <Card.Meta
                          title={`ID: ${item.image_id}`}
                          description={item.image?.filename || '未知'}
                        />
                      </Card>
                    </Col>
                  ))}
                </Row>
                <Pagination
                  current={pagination.current}
                  pageSize={pagination.pageSize}
                  total={pagination.total}
                  showSizeChanger
                  showTotal={(total) => `共 ${total} 张图片`}
                  onChange={(page, pageSize) => {
                    setPagination({ ...pagination, current: page, pageSize })
                    fetchImageList(page, pageSize)
                  }}
                  style={{ marginTop: 16, textAlign: 'right' }}
                />
              </>
            ) : (
              <Empty description="暂无图片" />
            )}
          </Spin>
        </Space>
      </Card>
    </div>
  )
}

export default FeatureStyleSubStyleImageManagement
