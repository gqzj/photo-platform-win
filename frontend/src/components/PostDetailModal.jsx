import React, { useState, useEffect } from 'react'
import { Modal, Descriptions, Image, List, Avatar, Tag, Space, Spin, message, Empty, Divider } from 'antd'
import { LikeOutlined, MessageOutlined, StarOutlined, UserOutlined, CalendarOutlined } from '@ant-design/icons'
import api from '../services/api'
import dayjs from 'dayjs'

const PostDetailModal = ({ postId, visible, onClose }) => {
  const [loading, setLoading] = useState(false)
  const [postDetail, setPostDetail] = useState(null)

  useEffect(() => {
    if (visible && postId) {
      fetchPostDetail()
    }
  }, [visible, postId])

  const fetchPostDetail = async () => {
    setLoading(true)
    try {
      const response = await api.get(`/posts/${postId}`)
      if (response.code === 200) {
        setPostDetail(response.data)
      } else {
        message.error(response.message || '获取帖子详情失败')
      }
    } catch (error) {
      message.error('获取帖子详情失败：' + (error.response?.data?.message || error.message))
      console.error('获取帖子详情错误:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatNumber = (num) => {
    if (!num) return '0'
    const n = parseInt(num)
    if (n >= 10000) {
      return (n / 10000).toFixed(1) + 'w'
    }
    return n.toString()
  }

  const getMediaUrl = (media) => {
    if (media.media_local_path && media.id) {
      return `/api/posts/media/item/${media.id}/content`
    }
    return media.media_url || null
  }

  // 组织评论为树形结构（父评论和子回复）
  const organizeComments = (comments) => {
    if (!comments || comments.length === 0) return []
    
    // 创建评论映射表（以comment_id为key）
    const commentMap = new Map()
    const rootComments = []
    
    // 第一遍遍历：创建所有评论的映射
    comments.forEach(comment => {
      commentMap.set(comment.comment_id, {
        ...comment,
        replies: []
      })
    })
    
    // 第二遍遍历：建立父子关系
    comments.forEach(comment => {
      const commentNode = commentMap.get(comment.comment_id)
      if (comment.parent_comment_id) {
        // 这是回复，添加到父评论的replies中
        const parentNode = commentMap.get(comment.parent_comment_id)
        if (parentNode) {
          parentNode.replies.push(commentNode)
        } else {
          // 如果找不到父评论，作为根评论处理
          rootComments.push(commentNode)
        }
      } else {
        // 这是根评论
        rootComments.push(commentNode)
      }
    })
    
    return rootComments
  }

  // 渲染单个评论（包括回复）
  const renderComment = (comment, isReply = false) => {
    return (
      <div key={comment.comment_id || comment.id} style={{ marginBottom: isReply ? 8 : 16 }}>
        <div style={{ 
          padding: isReply ? '8px 12px' : '12px',
          backgroundColor: isReply ? '#fafafa' : '#fff',
          borderLeft: isReply ? '3px solid #e0e0e0' : 'none',
          marginLeft: isReply ? 24 : 0,
          borderRadius: 4
        }}>
          <div style={{ display: 'flex', gap: 12 }}>
            <Avatar
              src={comment.user_avatar}
              icon={<UserOutlined />}
              size={isReply ? 'small' : 'default'}
              style={{ backgroundColor: '#87d068', flexShrink: 0 }}
            />
            <div style={{ flex: 1 }}>
              <div style={{ marginBottom: 8 }}>
                <Space>
                  <span style={{ fontSize: isReply ? 13 : 14, fontWeight: isReply ? 'normal' : 500 }}>
                    {comment.user_name || '匿名用户'}
                  </span>
                  {comment.like_count > 0 && (
                    <span style={{ color: '#999', fontSize: 12 }}>
                      <LikeOutlined /> {comment.like_count}
                    </span>
                  )}
                  {comment.comment_time && (
                    <span style={{ color: '#999', fontSize: 12 }}>
                      {dayjs(comment.comment_time).format('YYYY-MM-DD HH:mm')}
                    </span>
                  )}
                </Space>
              </div>
              <div style={{ 
                whiteSpace: 'pre-wrap', 
                fontSize: isReply ? 13 : 14,
                color: isReply ? '#666' : '#333',
                lineHeight: 1.6
              }}>
                {comment.content || '无内容'}
              </div>
            </div>
          </div>
        </div>
        
        {/* 递归渲染回复 */}
        {comment.replies && comment.replies.length > 0 && (
          <div style={{ marginTop: 8 }}>
            {comment.replies.map(reply => renderComment(reply, true))}
          </div>
        )}
      </div>
    )
  }

  if (!postDetail) {
    return null
  }

  const tags = Array.isArray(postDetail.tags) ? postDetail.tags : []
  const mediaList = postDetail.media || []
  const comments = postDetail.comments || []
  const organizedComments = organizeComments(comments)

  return (
    <Modal
      title="帖子详情"
      open={visible}
      onCancel={onClose}
      footer={null}
      width={900}
      style={{ top: 20 }}
    >
      <Spin spinning={loading}>
        <div style={{ maxHeight: '80vh', overflowY: 'auto' }}>
          {/* 基本信息 */}
          <Descriptions title="基本信息" bordered column={2} size="small">
            <Descriptions.Item label="标题" span={2}>
              {postDetail.title || '无标题'}
            </Descriptions.Item>
            <Descriptions.Item label="内容" span={2}>
              <div style={{ whiteSpace: 'pre-wrap', maxHeight: 200, overflowY: 'auto' }}>
                {postDetail.content || '无内容'}
              </div>
            </Descriptions.Item>
            <Descriptions.Item label="作者">
              <Space>
                <Avatar size="small" icon={<UserOutlined />} style={{ backgroundColor: '#87d068' }} />
                {postDetail.author_name || '未知用户'}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="作者粉丝数">
              {formatNumber(postDetail.author_follower_count)}
            </Descriptions.Item>
            <Descriptions.Item label="点赞数">
              <Space>
                <LikeOutlined />
                {formatNumber(postDetail.like_count)}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="评论数">
              <Space>
                <MessageOutlined />
                {formatNumber(postDetail.comment_count)}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="收藏数">
              <Space>
                <StarOutlined />
                {formatNumber(postDetail.collect_count)}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="作者获赞与收藏数">
              {formatNumber(postDetail.author_like_collect_count)}
            </Descriptions.Item>
            <Descriptions.Item label="发布时间">
              {postDetail.publish_time ? dayjs(postDetail.publish_time).format('YYYY-MM-DD HH:mm:ss') : '未知'}
            </Descriptions.Item>
            <Descriptions.Item label="抓取时间">
              {postDetail.crawl_time ? dayjs(postDetail.crawl_time).format('YYYY-MM-DD HH:mm:ss') : '未知'}
            </Descriptions.Item>
            <Descriptions.Item label="搜索关键词" span={2}>
              {postDetail.search_keyword || '无'}
            </Descriptions.Item>
            <Descriptions.Item label="标签" span={2}>
              {tags.length > 0 ? (
                <Space wrap>
                  {tags.map((tag, idx) => (
                    <Tag key={idx} color="pink">{tag}</Tag>
                  ))}
                </Space>
              ) : (
                '无标签'
              )}
            </Descriptions.Item>
          </Descriptions>

          <Divider />

          {/* 图片列表 */}
          <div style={{ marginBottom: 24 }}>
            <h3>图片 ({mediaList.length})</h3>
            {mediaList.length > 0 ? (
              <Image.PreviewGroup>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16 }}>
                  {mediaList.map((media) => {
                    const imageUrl = getMediaUrl(media)
                    return (
                      <div key={media.id} style={{ width: 200 }}>
                        {imageUrl ? (
                          <Image
                            src={imageUrl}
                            alt={`图片 ${media.sort_order}`}
                            width={200}
                            style={{ objectFit: 'cover' }}
                            preview={{
                              mask: '预览'
                            }}
                            onError={() => {
                              console.error(`图片加载失败 (Media ID: ${media.id})`)
                            }}
                          />
                        ) : (
                          <div style={{
                            width: 200,
                            height: 200,
                            backgroundColor: '#f5f5f5',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: '#999'
                          }}>
                            无图片
                          </div>
                        )}
                        {media.width && media.height && (
                          <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                            {media.width} × {media.height}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </Image.PreviewGroup>
            ) : (
              <Empty description="暂无图片" />
            )}
          </div>

          <Divider />

          {/* 评论列表 */}
          <div>
            <h3>评论 ({comments.length})</h3>
            {organizedComments.length > 0 ? (
              <div>
                {organizedComments.map(comment => (
                  <div key={comment.comment_id || comment.id} style={{ marginBottom: 16 }}>
                    {renderComment(comment)}
                  </div>
                ))}
              </div>
            ) : (
              <Empty description="暂无评论" />
            )}
          </div>
        </div>
      </Spin>
    </Modal>
  )
}

export default PostDetailModal

