import React, { useState, useEffect } from 'react'
import { Card, Tag, Spin, message, Button, Input, Space } from 'antd'
import { ReloadOutlined, SearchOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

const { Search } = Input

const KeywordView = () => {
  const navigate = useNavigate()
  const [keywords, setKeywords] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [filteredKeywords, setFilteredKeywords] = useState([])

  // 获取关键字列表
  const fetchKeywords = async () => {
    setLoading(true)
    try {
      const response = await api.get('/keyword-statistics')
      if (response.code === 200) {
        setKeywords(response.data.list || [])
        setFilteredKeywords(response.data.list || [])
      } else {
        message.error(response.message || '获取关键字列表失败')
      }
    } catch (error) {
      message.error('获取关键字列表失败：' + (error.response?.data?.message || error.message))
      console.error('获取关键字列表错误:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchKeywords()
  }, [])

  // 搜索过滤
  useEffect(() => {
    if (!searchKeyword) {
      setFilteredKeywords(keywords)
    } else {
      const filtered = keywords.filter(k => 
        k.keyword.toLowerCase().includes(searchKeyword.toLowerCase())
      )
      setFilteredKeywords(filtered)
    }
  }, [searchKeyword, keywords])

  // 刷新统计数据
  const handleRefresh = async () => {
    try {
      const response = await api.post('/keyword-statistics/refresh')
      if (response.code === 200) {
        message.success(response.message || '刷新成功')
        fetchKeywords()
      } else {
        message.error(response.message || '刷新失败')
      }
    } catch (error) {
      message.error('刷新失败：' + (error.response?.data?.message || error.message))
      console.error('刷新错误:', error)
    }
  }

  // 根据图片数量设置标签颜色
  const getTagColor = (count) => {
    if (count >= 1000) return 'red'
    if (count >= 500) return 'orange'
    if (count >= 100) return 'gold'
    if (count >= 50) return 'cyan'
    if (count >= 10) return 'blue'
    return 'default'
  }

  return (
    <div>
      <Card
        title="关键字查看"
        extra={
          <Space>
            <Search
              placeholder="搜索关键字"
              allowClear
              style={{ width: 300 }}
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              onSearch={(value) => setSearchKeyword(value)}
              enterButton={<SearchOutlined />}
            />
            <Button 
              icon={<ReloadOutlined />} 
              onClick={handleRefresh}
            >
              刷新统计
            </Button>
          </Space>
        }
      >
        <Spin spinning={loading}>
          {filteredKeywords.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
              {searchKeyword ? '未找到匹配的关键字' : '暂无关键字数据'}
            </div>
          ) : (
            <div style={{ 
              display: 'flex', 
              flexWrap: 'wrap', 
              gap: '12px',
              padding: '16px 0'
            }}>
              {filteredKeywords.map((item, index) => (
                <Tag
                  key={index}
                  color={getTagColor(item.image_count)}
                  style={{ 
                    fontSize: '14px',
                    padding: '8px 16px',
                    margin: 0,
                    cursor: 'pointer',
                    borderRadius: '4px'
                  }}
                  onClick={() => {
                    // 跳转到图片库并过滤该关键字
                    navigate(`/library/images?keyword=${encodeURIComponent(item.keyword)}`)
                  }}
                >
                  <span style={{ fontWeight: 'bold' }}>{item.keyword}</span>
                  <span style={{ marginLeft: '8px', opacity: 0.8 }}>
                    ({item.image_count} 张)
                  </span>
                </Tag>
              ))}
            </div>
          )}
        </Spin>
        
        {filteredKeywords.length > 0 && (
          <div style={{ 
            marginTop: '24px', 
            padding: '12px', 
            backgroundColor: '#f5f5f5', 
            borderRadius: '4px',
            fontSize: '14px',
            color: '#666'
          }}>
            共找到 <strong>{filteredKeywords.length}</strong> 个关键字，
            总计 <strong>{filteredKeywords.reduce((sum, item) => sum + item.image_count, 0)}</strong> 张图片
          </div>
        )}
      </Card>
    </div>
  )
}

export default KeywordView

