/**
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { RouteRecordRaw } from 'vue-router';

export { };

import 'vue-router';

declare module 'vue-router' {
  interface RouteMeta {
    // is optional
    icon: string;
    // must be declared by every route
    display_name: string;
    parent?: string;
    navParent?: string;
    showInMenu?: boolean;
    group?: string;
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        component: () => import('pages/IndexPage.vue'),
        name: 'dashboard',
        meta: { icon: 'dashboard', display_name: 'Dashboard' },
      },
      {
        path: 'proxy_jobs',
        name: 'proxy_jobs',
        component: () => import('src/pages/ProxyJobs.vue'),
        meta: {
          icon: 'work',
          parent: 'dashboard',
          display_name: 'Socks Jobs',
          showInMenu: true,
          group: 'Jobs and Playbooks',
        },
      },
      {
        path: 'proxy_jobs/:id',
        name: 'proxy_job',
        component: () => import('src/pages/ProxyJob.vue'),
        props: true,
        meta: { icon: 'work', parent: 'proxy_jobs', display_name: 'Socks Job' },
      },
      {
        path: 'proxy_jobs/add',
        name: 'add_proxy_job',
        component: () => import('src/pages/AddProxyJob.vue'),
        meta: {
          icon: 'add',
          parent: 'proxy_jobs',
          display_name: 'Add socks job',
        },
      },
      {
        path: 'proxy_jobs/add_from_template',
        name: 'add_proxy_job_from_template',
        component: () => import('src/pages/AddProxyJobTemplate.vue'),
        meta: {
          icon: 'add',
          parent: 'proxy_jobs',
          display_name: 'Add from template',
        },
      },
      {
        path: 'playbooks',
        name: 'playbooks',
        component: () => import('src/pages/JobChains.vue'),
        meta: {
          icon: 'menu_book',
          parent: 'dashboard',
          display_name: 'Playbooks',
          showInMenu: true,
          group: 'Jobs and Playbooks',
        },
      },
      {
        path: 'playbooks/:id',
        name: 'playbook',
        component: () => import('src/pages/JobChain.vue'),
        props: true,
        meta: { icon: 'link', parent: 'playbooks', display_name: 'Playbook' },
      },
      {
        path: 'playbooks/add',
        name: 'add_playbook',
        component: () => import('src/pages/AddProxyJobChain.vue'),
        meta: { icon: 'add', parent: 'playbooks', display_name: 'Add a playbook' },
      },
      {
        path: 'playbooks/add_from_template',
        name: 'add_playbook_from_template',
        component: () => import('src/pages/AddProxyJobChainFromTemplate.vue'),
        meta: {
          icon: 'add',
          parent: 'playbooks',
          display_name: 'Create a playbook from template',
        },
      },
      {
        path: 'playbooks/add_template',
        name: 'add_playbook_template',
        component: () => import('src/pages/AddChainTemplate.vue'),
        meta: {
          icon: 'add',
          parent: 'playbooks',
          display_name: 'Add a playbook template',
        },
      },
      {
        path: 'playbooks/add_template_ai',
        name: 'add_playbook_template_ai',
        component: () => import('src/pages/CreatePlaybookTemplateAI.vue'),
        meta: {
          icon: 'fas fa-robot',
          parent: 'playbooks',
          display_name: 'Add a playbook template with AI',
        },
      },
      {
        path: 'credentials',
        name: 'credentials',
        component: () => import('src/pages/CredentialsPage.vue'),
        meta: {
          icon: 'fingerprint',
          parent: 'dashboard',
          display_name: 'Credentials',
          showInMenu: true,
          group: 'Harbinger data',
        },
      },
      {
        path: 'credentials/add',
        component: () => import('src/pages/AddCredential.vue'),
        name: 'add_credential',
        meta: {
          icon: 'add',
          parent: 'credentials',
          display_name: 'Add a credential',
        },
      },
      {
        path: 'proxies',
        name: 'proxies',
        component: () => import('src/pages/ProxiesPage.vue'),
        meta: {
          icon: 'share',
          parent: 'dashboard',
          display_name: 'Socks Proxies',
          showInMenu: true,
          group: 'C2 Connectors',
        },
      },
      {
        path: 'proxies/add',
        name: 'proxy',
        component: () => import('src/pages/AddProxy.vue'),
        meta: {
          icon: 'add',
          parent: 'proxies',
          display_name: 'Proxy',
        },
      },
      {
        path: 'files',
        name: 'files',
        component: () => import('src/pages/FilesPage.vue'),
        meta: {
          icon: 'article',
          parent: 'dashboard',
          display_name: 'Files',
          showInMenu: true,
          group: 'Harbinger data',
        },
      },
      {
        path: 'files/add',
        name: 'add-file',
        component: () => import('src/pages/UploadFile.vue'),
        meta: {
          icon: 'add',
          parent: 'files',
          display_name: 'Upload file',
        },
      },
      {
        path: 'files/add_multiple',
        name: 'add-multiple-files',
        component: () => import('src/pages/UploadFiles.vue'),
        meta: {
          icon: 'add',
          parent: 'files',
          display_name: 'Upload files',
        },
      },
      {
        path: 'files/:id',
        name: 'file',
        component: () => import('src/pages/FilePage.vue'),
        props: true,
        meta: {
          icon: 'article',
          parent: 'files',
          display_name: 'File',
        },
      },
      {
        path: 'components',
        name: 'components',
        component: () => import('src/pages/ComponentsPage.vue'),
        meta: {
          icon: 'dns',
          parent: 'dashboard',
          display_name: 'Components',
        },
      },
      {
        path: 'domains',
        name: 'domains',
        component: () => import('src/pages/DomainPage.vue'),
        meta: {
          icon: 'corporate_fare',
          parent: 'dashboard',
          display_name: 'Domains',
          showInMenu: true,
          group: 'Harbinger data',
        },
      },
      {
        path: 'domains/add',
        component: () => import('src/pages/AddDomain.vue'),
        meta: {
          icon: 'add',
          parent: 'domains',
          display_name: 'Add a domain',
        },
      },
      {
        path: 'passwords',
        name: 'passwords',
        component: () => import('src/pages/PasswordPage.vue'),
        meta: {
          icon: 'key',
          parent: 'dashboard',
          display_name: 'Passwords',
          navParent: 'credentials',
          showInMenu: true,
        },
      },
      {
        path: 'kerberos',
        name: 'kerberos',
        component: () => import('src/pages/KerberosPage.vue'),
        meta: {
          icon: 'fas fa-dog',
          parent: 'dashboard',
          display_name: 'Kerberos',
          navParent: 'credentials',
          showInMenu: true,
        },
      },
      {
        path: 'passwords/add',
        component: () => import('src/pages/AddPassword.vue'),
        meta: {
          icon: 'add',
          parent: 'passwords',
          display_name: 'Add a password',
        },
      },
      {
        path: 'computers',
        name: 'computers',
        component: () => import('src/pages/GraphComputers.vue'),
        meta: {
          icon: 'computer',
          parent: 'dashboard',
          display_name: 'Computers',
          showInMenu: true,
          group: 'BloodHound',
        },
      },
      {
        path: 'users',
        name: 'users',
        component: () => import('src/pages/GraphUsers.vue'),
        meta: {
          icon: 'person',
          parent: 'dashboard',
          display_name: 'Users',
          showInMenu: true,
          group: 'BloodHound',
        },
      },
      {
        path: 'groups',
        name: 'groups',
        component: () => import('src/pages/GraphGroups.vue'),
        meta: {
          icon: 'group',
          parent: 'dashboard',
          display_name: 'Groups',
          showInMenu: true,
          group: 'BloodHound',
        },
      },
      {
        path: 'implants',
        name: 'implants',
        component: () => import('src/pages/C2Implants.vue'),
        meta: {
          icon: 'fas fa-virus',
          parent: 'dashboard',
          display_name: 'Implants',
          showInMenu: true,
          group: 'C2 Connectors',
        },
      },
      {
        path: 'implants/:id',
        name: 'implant',
        component: () => import('src/pages/C2Implant.vue'),
        props: true,
        meta: {
          icon: 'fas fa-virus',
          parent: 'implants',
          display_name: 'Implant',
        },
      },
      {
        path: 'implants/:id/tasks/:task_id',
        name: 'implant_task',
        component: () => import('src/pages/C2Task.vue'),
        props: true,
        meta: {
          icon: 'task',
          parent: 'implant',
          display_name: 'Task',
        },
      },
      {
        path: 'tasks/:task_id',
        name: 'c2_task',
        component: () => import('src/pages/C2Task.vue'),
        props: true,
        meta: {
          icon: 'task',
          parent: 'c2_tasks',
          display_name: 'Task',
        },
      },
      {
        path: 'task_output/:id',
        name: 'c2_task_output',
        component: () => import('src/pages/C2TaskOutput.vue'),
        props: true,
        meta: {
          icon: 'task',
          parent: 'c2_tasks',
          display_name: 'Task',
        },
      },
      {
        path: 'tasks',
        name: 'c2_tasks',
        component: () => import('src/pages/C2Tasks.vue'),
        props: true,
        meta: {
          icon: 'task',
          parent: 'dashboard',
          display_name: 'Tasks',
          showInMenu: true,
          group: 'C2 Connectors',
        },
      },
      {
        path: 'servers',
        name: 'servers',
        component: () => import('src/pages/C2Servers.vue'),
        meta: {
          icon: 'dns',
          parent: 'dashboard',
          display_name: 'Servers',
          showInMenu: true,
          group: 'C2 Connectors',
        },
      },
      {
        path: 'servers/add',
        name: 'add_server',
        component: () => import('src/pages/AddC2Server.vue'),
        props: true,
        meta: {
          icon: 'add',
          parent: 'servers',
          display_name: 'Add',
        },
      },
      {
        path: 'servers/:id',
        name: 'server',
        component: () => import('src/pages/C2Server.vue'),
        props: true,
        meta: {
          icon: 'dns',
          parent: 'servers',
          display_name: 'Server',
        },
      },
      {
        path: 'socks_servers',
        name: 'socks_servers',
        component: () => import('src/pages/SocksServers.vue'),
        meta: {
          icon: 'dns',
          parent: 'dashboard',
          display_name: 'Socks Servers',
          showInMenu: true,
          group: 'C2 Connectors',
        },
      },
      {
        path: 'c2_jobs/:id',
        name: 'c2_job',
        component: () => import('src/pages/C2Job.vue'),
        props: true,
        meta: {
          icon: 'fas fa-satellite-dish',
          parent: 'c2_jobs',
          display_name: 'C2 Job',
        },
      },
      {
        path: 'c2_jobs',
        name: 'c2_jobs',
        component: () => import('src/pages/C2Jobs.vue'),
        meta: {
          icon: 'fas fa-satellite-dish',
          parent: 'dashboard',
          display_name: 'C2 Jobs',
          showInMenu: true,
          group: 'Jobs and Playbooks',
        },
      },
      {
        path: 'c2_jobs/add_from_template',
        name: 'add_c2_job_from_template',
        component: () => import('src/pages/AddC2JobTemplate.vue'),
        meta: {
          icon: 'add',
          parent: 'c2_jobs',
          display_name: 'Add C2 Job',
        },
      },
      {
        path: 'output',
        name: 'output',
        component: () => import('src/pages/C2Output.vue'),
        meta: {
          icon: 'output',
          parent: 'dashboard',
          display_name: 'C2 Output',
          showInMenu: true,
          group: 'C2 Connectors',
        },
      },
      {
        path: 'processes',
        name: 'processes',
        component: () => import('src/pages/ProcessPage.vue'),
        meta: {
          icon: 'todo',
          parent: 'dashboard',
          display_name: 'Processes',
        },
      },
      {
        path: 'bloodhound_utils',
        name: 'bloodhound_utils',
        component: () => import('src/pages/BloodHoundUtils.vue'),
        meta: {
          icon: 'img:bloodhound.png',
          parent: 'dashboard',
          display_name: 'BloodHound Utils',
          showInMenu: true,
          group: 'BloodHound',
        },
      },
      {
        path: 'hosts',
        name: 'hosts',
        component: () => import('src/pages/HostsPage.vue'),
        props: true,
        meta: {
          icon: 'computer',
          parent: 'dashboard',
          display_name: 'Hosts',
          showInMenu: true,
          group: 'Harbinger data',
        },
      },
      {
        path: 'hosts/:id',
        name: 'host',
        component: () => import('src/pages/HostPage.vue'),
        props: true,
        meta: {
          icon: 'computer',
          parent: 'hosts',
          display_name: 'Host',
        },
      },
      {
        path: 'timeline',
        name: 'timeline',
        component: () => import('src/pages/TimeLine.vue'),
        props: true,
        meta: {
          icon: 'timeline',
          parent: 'dashboard',
          display_name: 'Timeline',
          showInMenu: true,
          group: 'Harbinger data',
        },
      },
      {
        path: 'timeline/create',
        name: 'create_timeline',
        component: () => import('src/pages/CreateTimeLine.vue'),
        props: true,
        meta: {
          icon: 'add',
          parent: 'timeline',
          display_name: 'Create new timeline',
        },
      },
      {
        path: 'labels',
        name: 'labels',
        component: () => import('src/pages/LabelsList.vue'),
        props: true,
        meta: {
          icon: 'label',
          parent: 'dashboard',
          display_name: 'Labels',
          showInMenu: true,
          group: 'Harbinger data',
        },
      },
      {
        path: 'labels/add',
        name: 'add_labels',
        component: () => import('src/pages/AddLabel.vue'),
        props: true,
        meta: {
          icon: 'add',
          parent: 'labels',
          display_name: 'Add',
        },
      },
      {
        path: 'situational_awareness',
        name: 'situational_awareness',
        component: () => import('src/pages/SituationalAwareness.vue'),
        props: true,
        meta: {
          icon: 'travel_explore',
          parent: 'dashboard',
          display_name: 'Situational Awareness',
          showInMenu: true,
          group: 'Harbinger data',
        },
      },
      {
        path: 'situational_awareness/add',
        name: 'add_situational_awareness',
        component: () => import('src/pages/AddSituationalAwareness.vue'),
        props: true,
        meta: {
          icon: 'add',
          parent: 'situational_awareness',
          display_name: 'Add',
        },
      },
      {
        path: 'shares',
        name: 'shares',
        component: () => import('src/pages/SharesPage.vue'),
        props: true,
        meta: {
          icon: 'folder_shared',
          parent: 'dashboard',
          display_name: 'Shares',
          showInMenu: true,
          group: 'Harbinger data',
        },
      },
      {
        path: 'shares/:id',
        name: 'share',
        component: () => import('src/pages/SharePage.vue'),
        props: true,
        meta: {
          icon: 'folder_shared',
          parent: 'shares',
          display_name: 'Share',
        },
      },
      {
        path: 'share_files',
        name: 'share_files',
        component: () => import('src/pages/ShareFiles.vue'),
        props: true,
        meta: {
          icon: 'folder_shared',
          parent: 'dashboard',
          display_name: 'Share files',
          navParent: 'shares',
          showInMenu: true,
        },
      },
      {
        path: 'hashes',
        name: 'hashes',
        component: () => import('src/pages/HashesPage.vue'),
        meta: {
          icon: 'tag',
          parent: 'dashboard',
          display_name: 'Hashes',
          navParent: 'credentials',
          showInMenu: true,
        },
      },
      {
        path: 'settings',
        name: 'settings',
        component: () => import('src/pages/SettingsPage.vue'),
        meta: {
          icon: 'settings',
          parent: 'dashboard',
          display_name: 'Settings',
        },
      },
      {
        path: 'actions',
        name: 'actions',
        component: () => import('src/pages/ActionsPage.vue'),
        meta: {
          icon: 'check_circle',
          parent: 'dashboard',
          display_name: 'Actions',
          showInMenu: true,
          group: 'Jobs and Playbooks',
        },
      },
      {
        path: 'certificates',
        name: 'certificates',
        component: () => import('src/pages/CertificateAuthoritiesPage.vue'),
        meta: {
          icon: 'verified_user',
          parent: 'dashboard',
          display_name: 'Certificates',
          showInMenu: true,
          group: 'Harbinger data',
        },
      },
      {
        path: 'certificate_authorities',
        name: 'certificate_authorities',
        component: () => import('src/pages/CertificateAuthoritiesPage.vue'),
        meta: {
          icon: 'badge',
          parent: 'dashboard',
          display_name: 'Certificate Authorities',
          navParent: 'certificates',
        },
      },
      {
        path: 'certificate_templates',
        name: 'certificate_templates',
        component: () => import('src/pages/CertificateTemplatesPage.vue'),
        meta: {
          icon: 'add_moderator',
          parent: 'dashboard',
          display_name: 'Certificate Templates',
          navParent: 'certificates',
        },
      },
      {
        path: 'issues',
        name: 'issues',
        component: () => import('src/pages/IssuePage.vue'),
        meta: {
          icon: 'priority_high',
          parent: 'dashboard',
          display_name: 'Issue',
          showInMenu: true,
          group: 'Harbinger data',
        },
      },
      {
        path: 'issues/add',
        name: 'add_issues',
        component: () => import('src/pages/AddIssue.vue'),
        meta: {
          icon: 'plus',
          parent: 'issues',
          display_name: 'Add Issue',
        },
      },
      {
        path: 'timeline/add',
        name: 'add_manual_timeline_tasks',
        component: () => import('src/pages/AddManualTimelineTask.vue'),
        meta: {
          icon: 'add',
          parent: 'timeline',
          display_name: 'Add',
        },
      },
      {
        path: 'highlights',
        name: 'highlights',
        component: () => import('src/pages/HighlightPage.vue'),
        meta: {
          icon: 'check_circle',
          parent: 'dashboard',
          display_name: 'Highlight',
          showInMenu: true,
          group: 'Harbinger data',
        },
      },
      {
        path: 'suggestions',
        name: 'suggestions',
        component: () => import('src/pages/SuggestionsPage.vue'),
        meta: {
          icon: 'fas fa-robot',
          parent: 'dashboard',
          display_name: 'Suggestions',
          showInMenu: true,
          group: 'AI',
        },
      },
      {
        path: 'suggestions/:id/create',
        name: 'suggestion_create',
        props: true,
        component: () => import('src/pages/SuggestionCreatePage.vue'),
        meta: {
          icon: 'add',
          parent: 'suggestion',
          display_name: 'Create',
        },
      },
      {
        path: 'suggestions/:id',
        name: 'suggestion',
        props: true,
        component: () => import('src/pages/SuggestionPage.vue'),
        meta: {
          icon: 'fas fa-robot',
          parent: 'suggestions',
          display_name: 'Suggestion',
        },
      },
      {
        path: 'suggestions/add',
        name: 'add_suggestions',
        component: () => import('src/pages/AddSuggestion.vue'),
        meta: {
          icon: 'fas fa-robot',
          parent: 'suggestions',
          display_name: 'Create new suggestion',
        },
      },
      {
        path: 'checklist',
        name: 'checklist',
        component: () => import('src/pages/ChecklistPage.vue'),
        meta: {
          icon: 'check_circle',
          parent: 'dashboard',
          display_name: 'Checklist',
        },
      },
      {
        path: 'objectives',
        name: 'objectives',
        component: () => import('src/pages/ObjectivesPage.vue'),
        meta: {
        icon: 'check_circle',
        parent: 'dashboard',
        display_name: 'Objectives',
        },
    },
    {
        path: 'objectives/add',
        name: 'add_objective',
        component: () => import('src/pages/AddObjective.vue'),
        meta: {
        icon: 'check_circle',
        parent: 'objectives',
        display_name: 'Objectives',
        },
    }
    ,
    {
        path: 'plans',
        name: 'plans',
        component: () => import('src/pages/PlanPage.vue'),
        meta: {
        icon: 'check_circle',
        parent: 'dashboard',
        display_name: 'Plans',
        showInMenu: true,
        group: 'AI',
        },
    },
    {
        path: 'plans/add',
        name: 'add_plan',
        component: () => import('src/pages/AddPlan.vue'),
        meta: {
        icon: 'check_circle',
        parent: 'plans',
        display_name: 'Add Plan',
        },
    },
    {
        path: 'plans/:id',
        name: 'plan',
        component: () => import('src/pages/Plan.vue'),
        props: true,
        meta: {
        icon: 'check_circle',
        parent: 'plans',
        display_name: 'Plan',
        },
    }
    ,
    {
        path: 'plan_steps',
        name: 'plan_steps',
        component: () => import('src/pages/PlanStepPage.vue'),
        meta: {
        icon: 'check_circle',
        parent: 'dashboard',
        display_name: 'PlanStep',
        },
    },
    {
        path: 'add_plan_steps',
        name: 'add_plan_steps',
        component: () => import('src/pages/AddPlanStep.vue'),
        meta: {
        icon: 'check_circle',
        parent: 'plan_steps',
        display_name: 'PlanStep',
        },
    }
    
    ],
  },
  {
    path: '/login',
    component: () => import('layouts/LoginLayout.vue'),
    children: [
      {
        path: '',
        name: 'login',
        component: () => import('pages/LoginPage.vue'),
      },
    ],
  },
  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
];

export default routes;
