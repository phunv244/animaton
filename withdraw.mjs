import { createPublicClient, createWalletClient, http, formatUnits, parseUnits, parseAbi } from 'viem';
import { base } from 'viem/chains';
import { privateKeyToAccount } from 'viem/accounts';
import fs from 'fs';
import path from 'path';

const USDC_BASE = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913';
const ERC20_ABI = parseAbi([
  'function balanceOf(address owner) view returns (uint256)',
  'function transfer(address to, uint256 amount) returns (bool)',
  'function decimals() view returns (uint8)'
]);

const walletPath = path.join(process.env.USERPROFILE || process.env.HOME, '.automaton', 'wallet.json');
if (!fs.existsSync(walletPath)) {
  console.error('Khong tim thay wallet.json tai:', walletPath);
  process.exit(1);
}

const walletData = JSON.parse(fs.readFileSync(walletPath, 'utf8'));
const account = privateKeyToAccount(walletData.privateKey);

const client = createPublicClient({
  chain: base,
  transport: http('https://mainnet.base.org')
});

const walletClient = createWalletClient({
  account,
  chain: base,
  transport: http('https://mainnet.base.org')
});

async function main() {
  const targetAddress = process.argv[2];

  console.log('==================================================');
  console.log('      CONWAY AUTOMATON - QUẢN LÝ & RÚT TIỀN      ');
  console.log('==================================================');
  console.log(`Dia chi vi Agent : ${account.address}`);
  console.log(`Private Key vi   : ${walletData.privateKey}`);
  console.log('--------------------------------------------------');

  const ethBalance = await client.getBalance({ address: account.address });
  const usdcBal = await client.readContract({
    address: USDC_BASE,
    abi: ERC20_ABI,
    functionName: 'balanceOf',
    args: [account.address]
  });

  const formattedEth = formatUnits(ethBalance, 18);
  const formattedUsdc = formatUnits(usdcBal, 6);

  console.log(`So du ETH (Base)  : ${formattedEth} ETH`);
  console.log(`So du USDC (Base) : ${formattedUsdc} USDC`);
  console.log('==================================================');

  if (!targetAddress) {
    console.log('\n[HUONG DAN RUT TIEN]:');
    console.log('1. Cach 1 (Rut tu dong bang script nay):');
    console.log('   Chay: node withdraw.mjs <DIA_CHI_VI_CUA_BAN>');
    console.log('   Vi du: node withdraw.mjs 0x1234567890abcdef1234567890abcdef12345678');
    console.log('\n2. Cach 2 (Rut truc tiep tren MetaMask / Rabby Wallet):');
    console.log('   - Mo MetaMask / Rabby tren trinh duyet.');
    console.log('   - Chon "Import Account" (Nhap tai khoan).');
    console.log('   - Dan Private Key o tren vao.');
    console.log('   - Chon mang Base. Ban se thay toan bo so du va co the chuyen ve vi chinh bat cu luc nao.');
    return;
  }

  if (!/^0x[a-fA-F0-9]{40}$/.test(targetAddress)) {
    console.error('Dia chi vi nhan khong hop le:', targetAddress);
    process.exit(1);
  }

  if (usdcBal === 0n && ethBalance === 0n) {
    console.log('Vi Agent hien chua co so du de rut.');
    return;
  }

  console.log(`Dang thuc hien lenh rut toan bo tien ve vi: ${targetAddress}...`);

  // Rut USDC
  if (usdcBal > 0n) {
    console.log(`-> Dang chuyen ${formattedUsdc} USDC...`);
    try {
      const hash = await walletClient.writeContract({
        address: USDC_BASE,
        abi: ERC20_ABI,
        functionName: 'transfer',
        args: [targetAddress, usdcBal]
      });
      console.log(`   [THANH CONG] Tx Hash: https://basescan.org/tx/${hash}`);
    } catch (err) {
      console.error(`   [THAT BAI]:`, err.message);
    }
  }

  // Rut ETH (de lai mot chut lam gas neu con)
  if (ethBalance > 0n) {
    const gasReserve = parseUnits('0.0001', 18); // Giu lai 0.0001 ETH phi gas
    if (ethBalance > gasReserve) {
      const ethToSend = ethBalance - gasReserve;
      console.log(`-> Dang chuyen ${formatUnits(ethToSend, 18)} ETH...`);
      try {
        const hash = await walletClient.sendTransaction({
          to: targetAddress,
          value: ethToSend
        });
        console.log(`   [THANH CONG] Tx Hash: https://basescan.org/tx/${hash}`);
      } catch (err) {
        console.error(`   [THAT BAI]:`, err.message);
      }
    }
  }

  console.log('\nHoan tat kiem tra & rut tien!');
}

main().catch(err => {
  console.error('Loi:', err);
  process.exit(1);
});
