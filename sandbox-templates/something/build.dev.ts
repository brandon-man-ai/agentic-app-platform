import { Template, defaultBuildLogger } from 'e2b'
import { template } from './template'

async function main() {
  await Template.build(template, {
    alias: 'something-dev',
    onBuildLogs: defaultBuildLogger(),
  });
}

main().catch(console.error);