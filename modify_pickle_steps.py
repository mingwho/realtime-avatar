"""
Modify the Ditto config pickle to reduce diffusion steps from 50 to 25
"""
import pickle
import sys

config_path = '/app/ditto-talkinghead/checkpoints/ditto_cfg/v0.4_hubert_cfg_pytorch.pkl'
backup_path = config_path + '.backup'

print(f"Loading config from: {config_path}")

# Load the pickle
with open(config_path, 'rb') as f:
    config = pickle.load(f)

print(f"\nConfig type: {type(config)}")
print(f"Config keys: {list(config.keys()) if isinstance(config, dict) else 'Not a dict'}")

# Find sampling_timesteps
if isinstance(config, dict):
    print("\n" + "="*60)
    print("SEARCHING FOR SAMPLING_TIMESTEPS...")
    print("="*60)
    
    found = False
    for key, value in config.items():
        if 'sampling' in str(key).lower() or 'timestep' in str(key).lower() or 'ddim' in str(key).lower():
            print(f"\n{key}: {value}")
            found = True
        elif isinstance(value, dict):
            for subkey, subval in value.items():
                if 'sampling' in str(subkey).lower() or 'timestep' in str(subkey).lower() or 'ddim' in str(subkey).lower():
                    print(f"\n{key}.{subkey}: {subval}")
                    found = True
    
    if not found:
        print("\n⚠️  No obvious sampling_timesteps field found")
        print("\nDumping entire config structure:")
        for key, value in config.items():
            print(f"\n{key}:")
            if isinstance(value, dict):
                for k, v in list(value.items())[:10]:  # First 10 items
                    print(f"  {k}: {v}")
                if len(value) > 10:
                    print(f"  ... ({len(value)} total items)")
            else:
                print(f"  {value}")
    
    # Try to modify
    print("\n" + "="*60)
    print("ATTEMPTING TO MODIFY CONFIG...")
    print("="*60)
    
    modified = False
    
    # Look for sampling_timesteps in top-level
    if 'sampling_timesteps' in config:
        old_val = config['sampling_timesteps']
        config['sampling_timesteps'] = 25
        print(f"✓ Modified top-level sampling_timesteps: {old_val} → 25")
        modified = True
    
    # Look in nested dicts
    for key, value in config.items():
        if isinstance(value, dict) and 'sampling_timesteps' in value:
            old_val = value['sampling_timesteps']
            value['sampling_timesteps'] = 25
            print(f"✓ Modified {key}.sampling_timesteps: {old_val} → 25")
            modified = True
    
    # Also try ddim_steps as alternative name
    if 'ddim_steps' in config:
        old_val = config['ddim_steps']
        config['ddim_steps'] = 25
        print(f"✓ Modified top-level ddim_steps: {old_val} → 25")
        modified = True
    
    for key, value in config.items():
        if isinstance(value, dict) and 'ddim_steps' in value:
            old_val = value['ddim_steps']
            value['ddim_steps'] = 25
            print(f"✓ Modified {key}.ddim_steps: {old_val} → 25")
            modified = True
    
    if modified:
        # Backup original
        import shutil
        shutil.copy2(config_path, backup_path)
        print(f"\n✓ Backed up original to: {backup_path}")
        
        # Save modified config
        with open(config_path, 'wb') as f:
            pickle.dump(config, f)
        print(f"✓ Saved modified config to: {config_path}")
        print("\n🎉 SUCCESS! Config modified to use 25 diffusion steps")
    else:
        print("\n⚠️  Could not find sampling_timesteps or ddim_steps to modify")
        print("Config may use different parameter names or structure")
else:
    print(f"\n⚠️  Config is not a dictionary (type: {type(config)})")
    print("Cannot easily modify non-dict config")
