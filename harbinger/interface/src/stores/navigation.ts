import { defineStore } from 'pinia';
import { RouteRecordRaw } from 'vue-router';
import routes from 'src/router/routes';

export interface MenuItem {
  name: string;
  displayName: string;
  icon: string;
  path: string;
  children: MenuItem[];
  group?: string;
}

export interface MenuGroup {
  name: string;
  items: MenuItem[];
}

function buildMenu(routes: readonly RouteRecordRaw[], navParent: string | null = null): MenuItem[] {
  const items = routes
    .filter(route => (navParent === null ? !route.meta?.navParent : route.meta?.navParent === navParent) && route.name && route.meta?.showInMenu)
    .map(route => {
      const item: MenuItem = {
        name: route.name as string,
        displayName: route.meta?.display_name || 'Unnamed',
        icon: route.meta?.icon || 'default_icon',
        path: route.path,
        children: [], // Children will be attached below
        group: route.meta?.group,
      };
      return item;
    });

  for (const item of items) {
    const children = buildMenu(routes, item.name);
    if (children.length > 0) {
      // This is a parent item. Create a link to itself and add it as the first child.
      const selfLink: MenuItem = { ...item, children: [] };
      item.children.push(selfLink, ...children);
    }
  }

  return items;
}

export const useNavigationStore = defineStore('navigation', {
  state: () => ({
    menuGroups: [] as MenuGroup[],
  }),
  actions: {
    generateMenu() {
      const mainLayoutRoutes = routes.find(r => r.path === '/')?.children || [];
      const menuItems = buildMenu(mainLayoutRoutes, null);

      const groups: { [key: string]: MenuItem[] } = {};
      for (const item of menuItems) {
        const groupName = item.group || 'Misc';
        if (!groups[groupName]) {
          groups[groupName] = [];
        }
        groups[groupName].push(item);
      }

      const groupOrder = ['Harbinger data', 'Jobs and Playbooks', 'AI', 'C2 Connectors', 'BloodHound'];

      this.menuGroups = Object.keys(groups).map(name => ({
        name,
        items: groups[name],
      })).sort((a, b) => {
        const indexA = groupOrder.indexOf(a.name);
        const indexB = groupOrder.indexOf(b.name);
        if (indexA === -1) return 1;
        if (indexB === -1) return -1;
        return indexA - indexB;
      });
    },
  },
});