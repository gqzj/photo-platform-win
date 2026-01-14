import React, { useState, useEffect } from 'react'
import { Layout, Menu } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  PictureOutlined,
  RobotOutlined,
  TagsOutlined,
  SettingOutlined,
  UnorderedListOutlined,
  KeyOutlined,
  FileImageOutlined,
  FileTextOutlined,
  FolderOutlined,
  AppstoreOutlined,
  ClearOutlined,
  TagOutlined,
  ExperimentOutlined,
  DatabaseOutlined,
  ToolOutlined,
  DeleteOutlined,
  BarChartOutlined,
  ProjectOutlined,
  BgColorsOutlined,
  SearchOutlined,
  FileSearchOutlined
} from '@ant-design/icons'

const { Header, Sider, Content } = Layout

const MainLayout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  
  // 根据当前路径确定需要展开的子菜单
  const getOpenKeys = () => {
    const path = location.pathname
    if (path.startsWith('/tagging/feature')) {
      return ['features-menu']
    }
    if (path.startsWith('/tagging/feature-group')) {
      return ['features-menu']
    }
    return []
  }
  
  const [openKeys, setOpenKeys] = useState(getOpenKeys())

  // 一级菜单配置
  const topMenuItems = [
    {
      key: 'library',
      icon: <PictureOutlined />,
      label: '图片库'
    },
    {
      key: 'crawler',
      icon: <RobotOutlined />,
      label: '爬虫'
    },
    {
      key: 'tagging',
      icon: <TagsOutlined />,
      label: '标注'
    },
    {
      key: 'sample-set',
      icon: <DatabaseOutlined />,
      label: '样本集'
    },
    {
      key: 'requirement',
      icon: <ProjectOutlined />,
      label: '需求'
    },
    {
      key: 'style',
      icon: <BgColorsOutlined />,
      label: '风格'
    },
    {
      key: 'lut-analysis',
      icon: <FileSearchOutlined />,
      label: 'Lut分析'
    },
    {
      key: 'tools',
      icon: <ToolOutlined />,
      label: '工具'
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置'
    }
  ]

  // 二级菜单配置（根据一级菜单选择）
  const getSubMenuItems = (topKey) => {
    const subMenus = {
      crawler: [
        {
          key: '/crawler/tasks',
          icon: <UnorderedListOutlined />,
          label: '任务管理'
        },
        {
          key: '/crawler/cookies',
          icon: <KeyOutlined />,
          label: 'Cookie管理'
        }
      ],
      library: [
        {
          key: '/library/images',
          icon: <FileImageOutlined />,
          label: '抓取图片库'
        },
        {
          key: '/semantic-search',
          icon: <SearchOutlined />,
          label: '语义搜索(修复中)'
        },
        {
          key: '/library/feature-query',
          icon: <SearchOutlined />,
          label: '特征组合查询'
        },
        {
          key: '/library/feature-analysis',
          icon: <BarChartOutlined />,
          label: '图片库特征分析'
        },
        {
          key: '/library/posts',
          icon: <FileTextOutlined />,
          label: '小红书帖子'
        },
        {
          key: '/library/keywords',
          icon: <TagOutlined />,
          label: '关键字查看'
        },
        {
          key: '/semantic-search/settings',
          icon: <SettingOutlined />,
          label: '语义搜索设置'
        },
        {
          key: '/library/recycle',
          icon: <DeleteOutlined />,
          label: '图片回收站'
        }
      ],
      tagging: [
        {
          key: 'features-menu',
          icon: <AppstoreOutlined />,
          label: '特征管理',
          children: [
            {
              key: '/tagging/features',
              icon: <UnorderedListOutlined />,
              label: '特征列表'
            },
            {
              key: '/tagging/feature-analysis',
              icon: <BarChartOutlined />,
              label: '特征分析'
            },
            {
              key: '/tagging/feature-groups',
              icon: <AppstoreOutlined />,
              label: '特征组管理'
            }
          ]
        },
        {
          key: '/tagging/data-cleaning',
          icon: <ClearOutlined />,
          label: '数据清洗任务'
        },
        {
          key: '/tagging/tagging-task',
          icon: <TagOutlined />,
          label: '数据打标任务'
        },
        {
          key: '/tagging/recycle',
          icon: <FileImageOutlined />,
          label: '图片回收站'
        }
      ],
      tools: [
        {
          key: '/tools/cleaning-test',
          icon: <ExperimentOutlined />,
          label: '图片清洗测试'
        },
        {
          key: '/tools/tagging-test',
          icon: <TagOutlined />,
          label: '数据打标测试'
        },
        {
          key: '/tools/lut-analysis-test',
          icon: <FileSearchOutlined />,
          label: 'LUT分析测试'
        },
        {
          key: '/tools/image-similarity-test',
          icon: <SearchOutlined />,
          label: '图片相似度测试'
        }
      ],
      'sample-set': [
        {
          key: '/sample-set/management',
          icon: <DatabaseOutlined />,
          label: '样本集管理'
        },
        {
          key: '/sample-set/view',
          icon: <FileImageOutlined />,
          label: '样本集查看'
        }
      ],
      requirement: [
        {
          key: '/requirement/management',
          icon: <ProjectOutlined />,
          label: '需求管理'
        }
      ],
      style: [
        {
          key: '/style/management',
          icon: <BgColorsOutlined />,
          label: '风格定义管理'
        },
        {
          key: '/style/manual',
          icon: <FileTextOutlined />,
          label: '手工风格定义'
        },
        {
          key: '/style/feature-style-definition',
          icon: <AppstoreOutlined />,
          label: '特征风格定义'
        },
        {
          key: '/style/match',
          icon: <SearchOutlined />,
          label: '风格匹配'
        }
      ],
      'lut-analysis': [
        {
          key: '/lut-analysis/files',
          icon: <FolderOutlined />,
          label: 'Lut文件管理'
        },
        {
          key: '/lut-analysis/sample-images',
          icon: <FileImageOutlined />,
          label: '样本图片管理'
        },
        {
          key: '/lut-analysis/cluster',
          icon: <AppstoreOutlined />,
          label: 'LUT聚类分析'
        },
        {
          key: '/lut-analysis/snapshots',
          icon: <FileImageOutlined />,
          label: 'LUT聚类快照'
        }
      ],
      settings: [
        {
          key: '/settings/directory',
          icon: <FolderOutlined />,
          label: '目录设置'
        }
      ]
    }
    return subMenus[topKey] || []
  }

  // 根据当前路径确定一级菜单
  const getCurrentTopMenu = () => {
    const path = location.pathname
    if (path.startsWith('/crawler')) return 'crawler'
    if (path.startsWith('/library')) return 'library'
    if (path.startsWith('/tagging')) return 'tagging'
    if (path.startsWith('/sample-set')) return 'sample-set'
    if (path.startsWith('/requirement')) return 'requirement'
    if (path.startsWith('/style')) return 'style'
    if (path.startsWith('/lut-analysis')) return 'lut-analysis'
    if (path.startsWith('/tools')) return 'tools'
    if (path.startsWith('/settings')) return 'settings'
    if (path.startsWith('/semantic-search')) return 'library' // 语义搜索属于图片库
    return 'library' // 默认
  }

  const currentTopMenu = getCurrentTopMenu()
  const subMenuItems = getSubMenuItems(currentTopMenu)

  const handleTopMenuClick = ({ key }) => {
    // 切换到一级菜单时，导航到该菜单的第一个子菜单或默认页面
    const defaultRoutes = {
      library: '/library/images',
      crawler: '/crawler/tasks',
      tagging: '/tagging/features',
      'sample-set': '/sample-set/management',
      requirement: '/requirement/management',
      style: '/style/management',
      'lut-analysis': '/lut-analysis/files',
      tools: '/tools/cleaning-test',
      settings: '/settings/directory'
    }
    navigate(defaultRoutes[key] || '/')
  }

  const handleSubMenuClick = ({ key }) => {
    // 如果是父菜单项（features-menu），导航到特征列表
    if (key === 'features-menu') {
      navigate('/tagging/features')
    } else {
      navigate(key)
    }
  }
  
  const handleOpenChange = (keys) => {
    setOpenKeys(keys)
  }
  
  // 当路径变化时，更新展开的菜单
  useEffect(() => {
    setOpenKeys(getOpenKeys())
  }, [location.pathname])

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          background: '#001529',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center'
        }}
      >
        <div
          style={{
            color: '#fff',
            fontSize: 20,
            fontWeight: 'bold',
            marginRight: 40
          }}
        >
          照片管理后台
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[currentTopMenu]}
          items={topMenuItems}
          onClick={handleTopMenuClick}
          style={{ flex: 1, minWidth: 0 }}
        />
      </Header>
      <Layout>
        {subMenuItems.length > 0 && (
          <Sider
            collapsible
            collapsed={collapsed}
            onCollapse={setCollapsed}
            theme="light"
            width={200}
            style={{
              background: '#fff',
              borderRight: '1px solid #f0f0f0'
            }}
          >
            <Menu
              theme="light"
              selectedKeys={[location.pathname]}
              openKeys={openKeys}
              mode="inline"
              items={subMenuItems}
              onClick={handleSubMenuClick}
              onOpenChange={handleOpenChange}
            />
          </Sider>
        )}
        <Layout>
          <Content
            style={{
              margin: '24px',
              padding: '24px',
              background: '#fff',
              minHeight: 280
            }}
          >
            {children}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  )
}

export default MainLayout
