import {
  Box,
  Flex,
  Icon,
  Text,
  IconButton,
  VStack,
  useColorModeValue,
  Tooltip,
  Divider,
} from '@chakra-ui/react'
import {
  FiHome,
  FiUsers,
  FiActivity,
  FiSettings,
  FiCpu,
  FiGitBranch,
  FiChevronLeft,
  FiChevronRight,
} from 'react-icons/fi'
import { useRouter } from 'next/router'
import Link from 'next/link'

interface SidebarProps {
  isCollapsed?: boolean
  onToggleCollapse?: () => void
  onClose?: () => void
}

interface NavItemProps {
  icon: any
  children: string
  href: string
  isCollapsed?: boolean
}

const NavItem = ({ icon, children, href, isCollapsed }: NavItemProps) => {
  const router = useRouter()
  const isActive = router.pathname === href
  const bg = useColorModeValue('gray.100', 'gray.700')
  const color = useColorModeValue('brand.600', 'brand.200')

  return (
    <Tooltip
      label={isCollapsed ? children : ''}
      placement="right"
      isDisabled={!isCollapsed}
    >
      <Link href={href} passHref>
        <Flex
          align="center"
          p="4"
          mx="4"
          borderRadius="lg"
          role="group"
          cursor="pointer"
          bg={isActive ? bg : 'transparent'}
          color={isActive ? color : undefined}
          _hover={{
            bg: bg,
            color: color,
          }}
        >
          <Icon
            mr={isCollapsed ? "0" : "4"}
            fontSize="16"
            as={icon}
          />
          {!isCollapsed && (
            <Text fontSize="sm" fontWeight={isActive ? "semibold" : "medium"}>
              {children}
            </Text>
          )}
        </Flex>
      </Link>
    </Tooltip>
  )
}

export default function Sidebar({ isCollapsed = false, onToggleCollapse, onClose }: SidebarProps) {
  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')

  return (
    <Box
      bg={bgColor}
      borderRight="1px"
      borderRightColor={borderColor}
      w={isCollapsed ? '20' : '64'}
      h="full"
      transition="width 0.2s"
      overflow="hidden"
    >
      {/* Logo */}
      <Flex
        h="20"
        alignItems="center"
        justifyContent={isCollapsed ? "center" : "space-between"}
        px={isCollapsed ? "0" : "8"}
      >
        {!isCollapsed && (
          <Text fontSize="2xl" fontWeight="bold" color="brand.500">
            AgentZ
          </Text>
        )}
        {onToggleCollapse && (
          <IconButton
            aria-label="Toggle sidebar"
            icon={isCollapsed ? <FiChevronRight /> : <FiChevronLeft />}
            onClick={onToggleCollapse}
            variant="ghost"
            size="sm"
          />
        )}
        {onClose && (
          <IconButton
            aria-label="Close sidebar"
            icon={<FiChevronLeft />}
            onClick={onClose}
            variant="ghost"
            size="sm"
          />
        )}
      </Flex>

      <VStack spacing="1" align="stretch">
        <NavItem icon={FiHome} href="/" isCollapsed={isCollapsed}>
          Dashboard
        </NavItem>
        <NavItem icon={FiCpu} href="/agents" isCollapsed={isCollapsed}>
          Agents
        </NavItem>
        <NavItem icon={FiGitBranch} href="/workflows" isCollapsed={isCollapsed}>
          Workflows
        </NavItem>
        <NavItem icon={FiActivity} href="/analytics" isCollapsed={isCollapsed}>
          Analytics
        </NavItem>

        <Divider my="4" />

        <NavItem icon={FiUsers} href="/team" isCollapsed={isCollapsed}>
          Team
        </NavItem>
        <NavItem icon={FiSettings} href="/settings" isCollapsed={isCollapsed}>
          Settings
        </NavItem>
      </VStack>
    </Box>
  )
} 