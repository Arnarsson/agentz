import { ReactNode, useState } from 'react'
import {
  Box,
  Flex,
  IconButton,
  useColorModeValue,
  useDisclosure,
  Drawer,
  DrawerContent,
  DrawerOverlay,
} from '@chakra-ui/react'
import { HamburgerIcon } from '@chakra-ui/icons'
import Sidebar from './Sidebar'
import Header from './Header'

interface MainLayoutProps {
  children: ReactNode
}

export default function MainLayout({ children }: MainLayoutProps) {
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)

  return (
    <Box minH="100vh" bg={useColorModeValue('gray.50', 'gray.900')}>
      {/* Desktop sidebar */}
      <Box
        display={{ base: 'none', md: 'block' }}
        w={isSidebarCollapsed ? '20' : '64'}
        position="fixed"
        h="full"
        transition="width 0.2s"
      >
        <Sidebar
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        />
      </Box>

      {/* Mobile drawer */}
      <Drawer
        autoFocus={false}
        isOpen={isOpen}
        placement="left"
        onClose={onClose}
        returnFocusOnClose={false}
        onOverlayClick={onClose}
        size="full"
      >
        <DrawerOverlay />
        <DrawerContent>
          <Sidebar onClose={onClose} />
        </DrawerContent>
      </Drawer>

      {/* Main content */}
      <Box ml={{ base: 0, md: isSidebarCollapsed ? '20' : '64' }} transition="margin 0.2s">
        <Flex
          direction="column"
          minH="100vh"
        >
          <Header
            onOpenSidebar={onOpen}
            showMenuButton={{ base: true, md: false }}
          />
          <Box
            as="main"
            flex="1"
            p="4"
            overflowY="auto"
          >
            {children}
          </Box>
        </Flex>
      </Box>
    </Box>
  )
} 