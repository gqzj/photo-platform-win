import React, { useState, useEffect } from 'react'
import { Card, Input, Select, Row, Col, Pagination, Tag, Image, Empty, Spin, message, Avatar, Space } from 'antd'
import { SearchOutlined, LikeOutlined, MessageOutlined, StarOutlined, UserOutlined, EyeOutlined } from '@ant-design/icons'
import api from '../services/api'
import dayjs from 'dayjs'
import PostDetailModal from '../components/PostDetailModal'

const { Search } = Input
const { Option } = Select

const PostList = () => {
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 12,
    total: 0
  })
  const [filters, setFilters] = useState({
    keyword: '',
    author_name: '',
    search_keyword: ''
  })
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedPostId, setSelectedPostId] = useState(null)
  // 移除imageUrlCache，直接使用API接口URL

  useEffect(() => {
    fetchData()
  }, [pagination.current, pagination.pageSize, filters])

  const fetchData = async () => {
    setLoading(true)
    try {
      const params = {
        page: pagination.current,
        page_size: pagination.pageSize,
        keyword: filters.keyword || undefined,
        author_name: filters.author_name || undefined,
        search_keyword: filters.search_keyword || undefined
      }
      
      const response = await api.get('/posts', { params })
      
      if (response.code === 200) {
        setPosts(response.data.list || [])
        setPagination(prev => ({
          ...prev,
          total: response.data.total || 0
        }))
      } else {
        message.error(response.message || '获取帖子列表失败')
      }
    } catch (error) {
      message.error('获取帖子列表失败：' + (error.response?.data?.message || error.message))
      console.error('获取帖子列表错误:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (value) => {
    setFilters(prev => ({ ...prev, keyword: value }))
    setPagination(prev => ({ ...prev, current: 1 }))
  }

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
    setPagination(prev => ({ ...prev, current: 1 }))
  }

  const handlePageChange = (page, pageSize) => {
    setPagination(prev => ({
      ...prev,
      current: page,
      pageSize: pageSize
    }))
  }

  const getImageUrl = (post) => {
    // 直接使用content接口获取图片内容
    return `/api/posts/media/${post.id}/content`
  }

  const formatNumber = (num) => {
    if (!num) return '0'
    const n = parseInt(num)
    if (n >= 10000) {
      return (n / 10000).toFixed(1) + 'w'
    }
    return n.toString()
  }

  const handleViewDetail = (postId) => {
    setSelectedPostId(postId)
    setDetailModalVisible(true)
  }

  const handleCloseDetail = () => {
    setDetailModalVisible(false)
    setSelectedPostId(null)
  }

  return (
    <div>
      <Card
        title="小红书帖子"
        extra={
          <div style={{ display: 'flex', gap: 8 }}>
            <Search
              placeholder="搜索帖子标题或内容"
              allowClear
              style={{ width: 300 }}
              onSearch={handleSearch}
              enterButton={<SearchOutlined />}
            />
            <Input
              placeholder="作者名称"
              allowClear
              style={{ width: 150 }}
              onChange={(e) => handleFilterChange('author_name', e.target.value)}
            />
            <Input
              placeholder="搜索关键词"
              allowClear
              style={{ width: 150 }}
              onChange={(e) => handleFilterChange('search_keyword', e.target.value)}
            />
          </div>
        }
      >
        <Spin spinning={loading}>
          {posts.length === 0 ? (
            <Empty description="暂无帖子" />
          ) : (
            <>
              <Row gutter={[16, 16]}>
                {posts.map((post) => {
                  const coverImageUrl = getImageUrl(post)
                  const tags = Array.isArray(post.tags) ? post.tags : []
                  
                  return (
                    <Col key={post.id} xs={24} sm={12} md={8} lg={6}>
                      <Card
                        hoverable
                        actions={[
                          <span key="view" onClick={() => handleViewDetail(post.id)} style={{ cursor: 'pointer' }}>
                            <EyeOutlined /> 查看详情
                          </span>
                        ]}
                        cover={
                          coverImageUrl ? (
                            <div style={{ 
                              width: '100%', 
                              aspectRatio: '3/4',
                              overflow: 'hidden',
                              backgroundColor: '#f5f5f5',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}>
                              <Image
                                src={coverImageUrl}
                                alt={post.title || '帖子封面'}
                                style={{ 
                                  width: '100%', 
                                  height: '100%', 
                                  objectFit: 'cover' 
                                }}
                                preview={{
                                  mask: '预览'
                                }}
                                onError={() => {
                                  console.error(`帖子封面图片加载失败 (ID: ${post.id})`)
                                }}
                              />
                            </div>
                          ) : (
                            <div style={{ 
                              width: '100%', 
                              aspectRatio: '3/4',
                              backgroundColor: '#f5f5f5',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              color: '#999'
                            }}>
                              无封面图
                            </div>
                          )
                        }
                        bodyStyle={{ padding: 16 }}
                      >
                        <div style={{ marginBottom: 12 }}>
                          {post.title && (
                            <div style={{ 
                              fontSize: 14, 
                              fontWeight: 'bold',
                              marginBottom: 8,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              display: '-webkit-box',
                              WebkitLineClamp: 2,
                              WebkitBoxOrient: 'vertical'
                            }}>
                              {post.title}
                            </div>
                          )}
                          {post.content && (
                            <div style={{ 
                              fontSize: 12, 
                              color: '#666',
                              marginBottom: 8,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              display: '-webkit-box',
                              WebkitLineClamp: 2,
                              WebkitBoxOrient: 'vertical'
                            }}>
                              {post.content}
                            </div>
                          )}
                        </div>
                        
                        <div style={{ marginBottom: 12 }}>
                          <Space>
                            <Avatar 
                              size="small" 
                              icon={<UserOutlined />} 
                              style={{ backgroundColor: '#87d068' }}
                            />
                            <span style={{ fontSize: 12, color: '#666' }}>
                              {post.author_name || '未知用户'}
                            </span>
                          </Space>
                        </div>

                        {tags.length > 0 && (
                          <div style={{ marginBottom: 12 }}>
                            {tags.slice(0, 3).map((tag, idx) => (
                              <Tag key={idx} size="small" color="pink">
                                {tag}
                              </Tag>
                            ))}
                            {tags.length > 3 && (
                              <Tag size="small">+{tags.length - 3}</Tag>
                            )}
                          </div>
                        )}

                        <div style={{ 
                          display: 'flex', 
                          justifyContent: 'space-between',
                          fontSize: 12,
                          color: '#999'
                        }}>
                          <Space>
                            <span>
                              <LikeOutlined /> {formatNumber(post.like_count)}
                            </span>
                            <span>
                              <MessageOutlined /> {formatNumber(post.comment_count)}
                            </span>
                            <span>
                              <StarOutlined /> {formatNumber(post.collect_count)}
                            </span>
                          </Space>
                          {post.crawl_time && (
                            <span>
                              {dayjs(post.crawl_time).format('MM-DD')}
                            </span>
                          )}
                        </div>
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
                  showQuickJumper
                  showTotal={(total) => `共 ${total} 条帖子`}
                  onChange={handlePageChange}
                  onShowSizeChange={handlePageChange}
                  pageSizeOptions={['12', '24', '48']}
                />
              </div>
            </>
          )}
        </Spin>
      </Card>

      {/* 帖子详情弹窗 */}
      <PostDetailModal
        postId={selectedPostId}
        visible={detailModalVisible}
        onClose={handleCloseDetail}
      />
    </div>
  )
}

export default PostList

