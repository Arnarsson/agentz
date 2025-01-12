import {
  Box,
  Flex,
  IconButton,
  Button,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  MenuDivider,
  useColorModeValue,
  Text,
  HStack,
  Avatar,
  Badge,
  Tooltip,
  ResponsiveValue,
} from '@chakra-ui/react'
import {
  HamburgerIcon,
  BellIcon,
  ChevronDownIcon,
} from '@chakra-ui/icons'
import { FiSettings, FiHelpCircle, FiLogOut } from 'react-icons/fi'

interface HeaderProps {
  onOpenSidebar: () => void
  showMenuButton: ResponsiveValue<boolean>
}

export default function Header({ onOpenSidebar, showMenuButton }: HeaderProps) {
  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')

  return (
    <Box
      as="header"
      bg={bgColor}
      borderBottom="1px"
      borderBottomColor={borderColor}
      px="4"
      position="sticky"
      top="0"
      zIndex="sticky"
    >
      <Flex h="16" alignItems="center" justifyContent="space-between">
        <HStack spacing="4">
          {showMenuButton && (
            <IconButton
              aria-label="Open sidebar"
              icon={<HamburgerIcon />}
              onClick={onOpenSidebar}
              variant="ghost"
              size="md"
            />
          )}
          <Text fontSize="lg" fontWeight="semibold" color="brand.500" display={{ base: 'none', md: 'block' }}>
            Dashboard
          </Text>
        </HStack>

        <HStack spacing="4">
          {/* Quick Actions */}
          <Button
            variant="ghost"
            leftIcon={<FiHelpCircle />}
            size="sm"
            display={{ base: 'none', md: 'flex' }}
          >
            Help
          </Button>

          {/* Notifications */}
          <Menu>
            <Tooltip label="Notifications">
              <MenuButton
                as={IconButton}
                aria-label="Notifications"
                icon={
                  <Box position="relative">
                    <BellIcon />
                    <Badge
                      position="absolute"
                      top="-1"
                      right="-1"
                      colorScheme="red"
                      variant="solid"
                      borderRadius="full"
                      boxSize="2"
                      p="0"
                    />
                  </Box>
                }
                variant="ghost"
              />
            </Tooltip>
            <MenuList>
              <MenuItem>New Agent Available</MenuItem>
              <MenuItem>Workflow Completed</MenuItem>
              <MenuItem>System Update</MenuItem>
              <MenuDivider />
              <MenuItem>View All Notifications</MenuItem>
            </MenuList>
          </Menu>

          {/* User Menu */}
          <Menu>
            <MenuButton
              as={Button}
              variant="ghost"
              rightIcon={<ChevronDownIcon />}
              display="flex"
              alignItems="center"
            >
              <HStack spacing="3">
                <Avatar size="sm" name="User Name" src="/avatar-placeholder.jpg" />
                <Box display={{ base: 'none', md: 'block' }}>
                  <Text size="sm" fontWeight="medium">
                    User Name
                  </Text>
                  <Text size="xs" color="gray.500">
                    admin@example.com
                  </Text>
                </Box>
              </HStack>
            </MenuButton>
            <MenuList>
              <MenuItem icon={<FiSettings />}>Settings</MenuItem>
              <MenuItem icon={<FiHelpCircle />}>Help & Support</MenuItem>
              <MenuDivider />
              <MenuItem icon={<FiLogOut />} color="red.400">
                Sign Out
              </MenuItem>
            </MenuList>
          </Menu>
        </HStack>
      </Flex>
    </Box>
  )
} 